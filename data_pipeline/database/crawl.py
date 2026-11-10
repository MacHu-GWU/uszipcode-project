# -*- coding: utf-8 -*-

"""
Run one crawler: fetch (cached) -> parse (offline) -> each claimed Field reads its
value from the source rows -> check the output contract -> write.

The output contract (rules D1-D7) is checked before anything is written; on any
error the previous output stays. A crawler output is ``<name>.csv`` (header
``zipcode`` + the claimed Fields, one row per ZIP in the source, sorted, NULL =
empty cell; a history crawler has ``zipcode,year`` and one row per ZIP and year)
plus ``<name>.json`` (counts and the manifest of the downloads).
Keys are normalized with ``normalize_zip``; keys that are not ZIPs (``00000``,
``99999``, text) are skipped and counted.
"""

import collections.abc
import csv
import json
import math
import os
import typing

from ..zipcodes import normalize_zip
from . import fetch
from .core import ContractError, Crawler, Field, Paths, PipelineError

MAX_LISTED = 20
MAX_CELL_CHARS = 1 << 26  # a text value may be long (a GeoJSON boundary); the csv module allows 131,072 by default


def _null(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def coerce(field: Field, value):
    """Check ``value`` against the Field's dtype. Returns ``(value, error)``; error is ``(rule, short text)`` or None."""
    if _null(value):
        return None, None
    if field.dtype is int:
        if isinstance(value, bool) or not isinstance(value, int):
            return None, ("D3", "%r is not an int" % (value,))
        return value, None
    if field.dtype is float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None, ("D3", "%r is not a float" % (value,))
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return None, ("D6", "%r is not a finite number" % (value,))
        return value, None
    if not isinstance(value, str):
        return None, ("D3", "%r is not a str" % (value,))
    return value.strip(), None


def _year(value) -> typing.Optional[int]:
    try:
        year = int(value)
    except (TypeError, ValueError):
        return None
    return year if 1900 <= year <= 2100 else None


def _label(key) -> str:
    return "zipcode %s, year %d" % key if isinstance(key, tuple) else "zipcode %s" % key


def check_rows(crawler: Crawler, catalog: typing.Dict[str, Field],
               rows: typing.Iterable) -> typing.Tuple[typing.List[tuple], dict]:
    """
    Let each claimed Field read its value from the source rows of ``parse()`` and apply rules D1-D7.
    Returns ``(records, stats)``: records are ``(key, [value per claimed Field])`` sorted by key; the key
    is the zipcode, or ``(zipcode, year)`` for a history crawler.
    """
    claims = list(crawler.fields)
    errors, records, first_row = [], {}, {}
    skipped, skipped_examples, n_rows = 0, [], 0
    for i, row in enumerate(rows, start=1):
        n_rows += 1
        if not (isinstance(row, tuple) and len(row) == 2 and isinstance(row[1], collections.abc.Mapping)):
            errors.append("row %d: parse() must yield (zipcode, {column: value}), got %r" % (i, row))
            continue
        key, source_row = row
        z = normalize_zip(key)
        if z is None:
            skipped += 1
            if len(skipped_examples) < 5:
                skipped_examples.append(str(key))
            continue
        if crawler.history:
            year = _year(source_row.get("year"))
            if year is None:
                errors.append("[D7] row %d, zipcode %s: a history source row needs a year, got %r"
                              % (i, z, source_row.get("year")))
                continue
            z = (z, year)
        if z in records:
            errors.append("[D1] row %d: %s appears again (first at row %d): aggregate multi-row sources in parse()"
                          % (i, _label(z), first_row[z]))
            continue
        out = []
        for name in claims:
            try:
                raw_value = catalog[name].extract(source_row)
            except Exception as e:  # the source column is gone, or a value cannot be converted
                errors.append("[D2] row %d, %s, field %s: cannot read it from the source row: %s: %s"
                              % (i, _label(z), name, type(e).__name__, e))
                out.append(None)
                continue
            value, error = coerce(catalog[name], raw_value)
            if error:
                errors.append("[%s] row %d, %s, field %s: %s" % (error[0], i, _label(z), name, error[1]))
            out.append(value)
        records[z], first_row[z] = out, i
    if n_rows == 0 or (not records and not errors):
        errors.append("[D5] parse() returned no usable rows (%d rows, %d skipped keys)" % (n_rows, skipped))
    non_null = {name: sum(1 for vals in records.values() if vals[j] is not None) for j, name in enumerate(claims)}
    if records:
        for name in claims:
            if non_null[name] == 0:
                errors.append("[D4] Field %r is NULL in every row: the source probably changed its header" % name)
    if errors:
        lines = errors[:MAX_LISTED]
        if len(errors) > MAX_LISTED:
            lines.append("... and %d more" % (len(errors) - MAX_LISTED))
        raise ContractError("crawler %r: output contract failed: %d problem(s)\n  %s"
                            % (crawler.name, len(errors), "\n  ".join(lines)))
    stats = {"rows": len(records), "skipped_keys": skipped, "skipped_examples": skipped_examples,
             "non_null": non_null}
    return sorted(records.items()), stats


def format_value(value) -> str:
    """CSV cell: NULL -> empty, int -> str(), float -> repr() (round-trips exactly), str as is."""
    if value is None:
        return ""
    if isinstance(value, float):
        return repr(value)
    return str(value)


def write_csv(path: str, header: typing.List[str], rows: typing.Iterable[typing.Sequence]) -> None:
    """UTF-8 without BOM, ``\\n`` line endings, written through ``.part`` + ``os.replace``."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    part = path + ".part"
    with open(part, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(header)
        for row in rows:  # format_value, inlined: this loop runs once per cell of the database
            writer.writerow(["" if v is None else repr(v) if v.__class__ is float else str(v) for v in row])
    replace(part, path)


def write_json(path: str, data: dict, sort_keys: bool = True) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    part = path + ".part"
    with open(part, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=2, sort_keys=sort_keys)
        fh.write("\n")
    replace(part, path)


def replace(part: str, path: str) -> None:
    try:
        os.replace(part, path)
    except PermissionError:
        raise PipelineError("cannot replace %s: close programs that have it open (Excel, DB Browser) and run again"
                            % path) from None


def output_paths(crawler: Crawler, out_dir: str) -> typing.Tuple[str, str]:
    return os.path.join(out_dir, crawler.name + ".csv"), os.path.join(out_dir, crawler.name + ".json")


def key_columns(crawler: Crawler) -> typing.List[str]:
    return ["zipcode", "year"] if crawler.history else ["zipcode"]


def write_output(crawler: Crawler, records, meta: dict, out_dir: str) -> str:
    csv_path, json_path = output_paths(crawler, out_dir)
    write_csv(csv_path, key_columns(crawler) + list(crawler.fields),
              ((list(key) if isinstance(key, tuple) else [key]) + vals for key, vals in records))
    write_json(json_path, meta)
    return csv_path


def read_output(crawler: Crawler, catalog: typing.Dict[str, Field],
                out_dir: str) -> typing.Dict[typing.Any, typing.Dict[str, typing.Any]]:
    """
    ``{key: {field: value}}`` from ``<name>.csv`` (the key is the zipcode, or ``(zipcode, year)`` for a
    history crawler); checks it against the crawler's current claims (B1-B3).
    """
    csv_path, json_path = output_paths(crawler, out_dir)
    for p in (csv_path, json_path):
        if not os.path.exists(p):
            raise PipelineError("[B1] crawler output missing: %s; run: mise run crawler-%s" % (p, crawler.name))
    keys = key_columns(crawler)
    expected = keys + list(crawler.fields)
    names = list(crawler.fields)
    dtypes = [catalog[name].dtype for name in names]
    out = {}
    csv.field_size_limit(max(csv.field_size_limit(), MAX_CELL_CHARS))
    with open(csv_path, encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader, [])
        if header != expected:
            raise ContractError('[B2] crawler output %s is stale: its header is "%s" but %s claims "%s"; run: mise run crawler-%s'
                                % (csv_path, ",".join(header), crawler.name, ",".join(crawler.fields), crawler.name))
        for line, row in enumerate(reader, start=2):
            key = None
            if len(row) == len(expected):  # an empty line is a row without cells
                key = row[0] if not crawler.history else (row[0], _year(row[1]))
            if key is None or not _is_written_zip(row[0]) or key in out or (crawler.history and key[1] is None):
                raise ContractError("[B3] %s line %d: not a valid row: %r" % (csv_path, line, row))
            cells = row[len(keys):]
            try:
                out[key] = {name: None if cell == "" else dtype(cell) for name, dtype, cell in zip(names, dtypes, cells)}
            except ValueError:
                name, dtype, cell = next((n, d, c) for n, d, c in zip(names, dtypes, cells) if not _converts(d, c))
                raise ContractError("[B3] %s line %d: %r is not a valid %s for field %s"
                                    % (csv_path, line, cell, dtype.__name__, name)) from None
    return out


def _is_written_zip(value: str) -> bool:
    """Same as ``normalize_zip(value) == value``, for the zipcodes this module wrote; cheaper on large outputs."""
    return len(value) == 5 and value.isdigit() and value not in ("00000", "99999")


def _converts(dtype: type, cell: str) -> bool:
    try:
        dtype(cell) if cell != "" else None
    except ValueError:
        return False
    return True


def read_meta(crawler: Crawler, out_dir: str) -> dict:
    with open(output_paths(crawler, out_dir)[1], encoding="utf-8") as fh:
        return json.load(fh)


def check_downloads(crawler: Crawler, meta: dict, out_dir: str) -> None:
    """B2: the output was made from the files the crawler declares now (a new year changes the URLs)."""
    made_from = {filename: entry.get("url") for filename, entry in meta.get("downloads", {}).items()}
    declared = {d.filename: d.url for d in crawler.downloads}
    changed = sorted(f for f in set(made_from) | set(declared) if made_from.get(f) != declared.get(f))
    if changed:
        raise ContractError("[B2] crawler output %s is stale: %s declares other downloads now (%s); run: mise run crawler-%s"
                            % (output_paths(crawler, out_dir)[0], crawler.name, ", ".join(changed), crawler.name))


def run_crawler(crawler: Crawler, fields: typing.Sequence[Field], paths: Paths,
                refresh: bool = False, force: bool = False) -> dict:
    """Fetch, parse, check and write one crawler. Returns a summary for the CLI."""
    catalog = {f.name: f for f in fields}
    files, requests = fetch.fetch_all(crawler, paths.cache_dir, refresh=refresh, force=force)
    try:
        records, stats = check_rows(crawler, catalog, crawler.parse(files))
    except PipelineError:
        raise
    except Exception as e:  # a parser bug or a changed source format
        raise ContractError("crawler %r: parse() failed: %s: %s" % (crawler.name, type(e).__name__, e)) from e
    downloads = fetch.manifest_entries(crawler, paths.cache_dir)
    meta = dict(stats, crawler=crawler.name,
                fields=[{"name": n, "dtype": catalog[n].dtype.__name__} for n in crawler.fields],
                downloads=downloads)
    path = write_output(crawler, records, meta, paths.crawler_out_dir)
    return {"crawler": crawler.name, "requests": requests, "files": len(files), "rows": stats["rows"],
            "skipped_keys": stats["skipped_keys"], "path": path,
            "fetched": sorted({e.get("fetched_at_utc", "")[:10] for e in downloads.values()})}
