# -*- coding: utf-8 -*-

"""
Run one crawler: fetch (cached) -> parse (offline) -> check the output contract -> write.

The output contract (rules D1-D6) is checked before anything is written; on any
error the previous output stays. A crawler output is ``<name>.csv`` (header
``zipcode`` + the claimed Fields, one row per ZIP in the source, sorted, NULL =
empty cell) plus ``<name>.json`` (counts and the manifest of the downloads).
Keys are normalized with ``normalize_zip``; keys that are not ZIPs (``00000``,
``99999``, text) are skipped and counted.
"""

import csv
import json
import math
import os
import typing

from ..zipcode_universe.sources import normalize_zip
from . import fetch
from .core import ContractError, Crawler, Field, Paths, PipelineError

MAX_LISTED = 20


def _null(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _coerce(field: Field, value):
    """Return ``(value, error)``; error is ``(rule, short text)`` or None."""
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


def check_rows(crawler: Crawler, catalog: typing.Dict[str, Field],
               rows: typing.Iterable) -> typing.Tuple[typing.List[tuple], dict]:
    """
    Apply rules D1-D6 to the rows of ``parse()``.
    Returns ``(records, stats)``: records are ``(zipcode, [value per claimed Field])`` sorted by zipcode.
    """
    claims = list(crawler.fields)
    claimed = set(claims)
    errors, records, first_row = [], {}, {}
    skipped, skipped_examples, n_rows = 0, [], 0
    for i, row in enumerate(rows, start=1):
        n_rows += 1
        if not (isinstance(row, tuple) and len(row) == 2 and isinstance(row[1], dict)):
            errors.append("row %d: parse() must yield (zipcode, {field: value}), got %r" % (i, row))
            continue
        key, values = row
        z = normalize_zip(key)
        if z is None:
            skipped += 1
            if len(skipped_examples) < 5:
                skipped_examples.append(str(key))
            continue
        if z in records:
            errors.append("[D1] row %d: zipcode %s appears again (first at row %d): aggregate multi-row sources in parse()"
                          % (i, z, first_row[z]))
            continue
        for k in values:
            if k not in claimed:
                errors.append("[D2] row %d, zipcode %s: %r is not a Field of crawler %r" % (i, z, k, crawler.name))
        out = []
        for name in claims:
            value, error = _coerce(catalog[name], values.get(name))
            if error:
                errors.append("[%s] row %d, zipcode %s, field %s: %s" % (error[0], i, z, name, error[1]))
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
        for row in rows:
            writer.writerow([format_value(v) for v in row])
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


def write_output(crawler: Crawler, records, meta: dict, out_dir: str) -> str:
    csv_path, json_path = output_paths(crawler, out_dir)
    write_csv(csv_path, ["zipcode"] + list(crawler.fields), ([z] + vals for z, vals in records))
    write_json(json_path, meta)
    return csv_path


def read_output(crawler: Crawler, catalog: typing.Dict[str, Field],
                out_dir: str) -> typing.Dict[str, typing.Dict[str, typing.Any]]:
    """``{zipcode: {field: value}}`` from ``<name>.csv``; checks it against the crawler's current claims (B1-B3)."""
    csv_path, json_path = output_paths(crawler, out_dir)
    for p in (csv_path, json_path):
        if not os.path.exists(p):
            raise PipelineError("[B1] crawler output missing: %s; run: mise run crawler-%s" % (p, crawler.name))
    expected = ["zipcode"] + list(crawler.fields)
    out = {}
    with open(csv_path, encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader, [])
        if header != expected:
            raise ContractError('[B2] crawler output %s is stale: its header is "%s" but %s claims "%s"; run: mise run crawler-%s'
                                % (csv_path, ",".join(header), crawler.name, ",".join(crawler.fields), crawler.name))
        for line, row in enumerate(reader, start=2):
            if len(row) != len(expected) or normalize_zip(row[0]) != row[0] or row[0] in out:
                raise ContractError("[B3] %s line %d: not a valid row: %r" % (csv_path, line, row))
            values = {}
            for name, cell in zip(crawler.fields, row[1:]):
                dtype = catalog[name].dtype
                try:
                    values[name] = None if cell == "" else dtype(cell)
                except ValueError:
                    raise ContractError("[B3] %s line %d: %r is not a valid %s for field %s"
                                        % (csv_path, line, cell, dtype.__name__, name)) from None
            out[row[0]] = values
    return out


def read_meta(crawler: Crawler, out_dir: str) -> dict:
    with open(output_paths(crawler, out_dir)[1], encoding="utf-8") as fh:
        return json.load(fh)


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
