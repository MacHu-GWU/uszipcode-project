# -*- coding: utf-8 -*-

"""
Build the database: the PK set LEFT JOIN every crawler output.

Rows are the PKs, columns are ``zipcode`` plus every Field in catalog order, and
NULL means "no value" (normal: a PO box ZIP has no Census statistics). Building
never downloads anything, so switching PK sets is free.

Outputs in ``output/``: ``db_<set>.sqlite`` (table ``zipcode_data``),
``db_<set>.csv`` (the same table) and ``db_<set>_coverage.json``.
"""

import csv
import os
import re
import sqlite3
import typing

from ..zipcode_universe.sources import normalize_zip
from .core import Crawler, Field, Paths, PkSetError, SQL_TYPES
from .crawl import read_meta, read_output, replace, write_csv, write_json
from .registry import owners, require_valid

#: the minimal example: two standard ZIPs and a PO box ZIP without a ZCTA (so no Census values)
DEMO_PKS = ("10001", "20013", "20037")
TABLE = "zipcode_data"
SET_NAME = re.compile(r"^[A-Za-z0-9_-]+$")


def _read_pk_csv(path: str, label: str) -> typing.List[str]:
    with open(path, encoding="utf-8-sig", newline="") as fh:  # -sig: Excel writes a BOM
        reader = csv.reader(fh)
        header = [h.strip() for h in next(reader, [])]
        if "zipcode" not in header:
            raise PkSetError("PK set %r has no 'zipcode' column" % label)
        i = header.index("zipcode")
        pks, line_of = [], {}
        for line, row in enumerate(reader, start=2):
            if not row:
                continue
            z = row[i].strip() if len(row) > i else ""
            if normalize_zip(z) != z:
                raise PkSetError("PK set %r: line %d: %r is not a 5-digit ZIP" % (label, line, z))
            if z in line_of:
                raise PkSetError("PK set %r: duplicate ZIP %r (lines %d and %d)" % (label, z, line_of[z], line))
            line_of[z] = line
            pks.append(z)
    if not pks:
        raise PkSetError("PK set %r is empty" % label)
    return pks


def load_pk_set(spec: str, paths: Paths) -> typing.Tuple[str, typing.List[str]]:
    """``demo``, ``full`` (all ZIPs of zipcode_universe.csv) or the path of a CSV file with a ``zipcode`` column."""
    if spec == "demo":
        return "demo", sorted(DEMO_PKS)
    if spec == "full":
        if not os.path.exists(paths.universe_csv):
            raise PkSetError("%s not found; run: mise run zipcode-universe" % paths.universe_csv)
        return "full", sorted(_read_pk_csv(paths.universe_csv, "full"))
    if not os.path.isfile(spec):
        raise PkSetError("PK set %r is not 'demo', 'full' or an existing CSV file" % spec)
    name = os.path.splitext(os.path.basename(spec))[0]
    if not SET_NAME.match(name):
        raise PkSetError("PK set file name %r may only use A-Z a-z 0-9 _ -" % name)
    return name, sorted(_read_pk_csv(spec, name))


def assemble(pks: typing.Sequence[str], fields: typing.Sequence[Field], owner: typing.Dict[str, str],
             outputs: typing.Dict[str, typing.Dict[str, dict]]) -> typing.List[list]:
    """Pure left join: one row per PK, ``[zipcode] + [value per Field]``."""
    return [[pk] + [outputs[owner[f.name]].get(pk, {}).get(f.name) for f in fields] for pk in pks]


def _write_sqlite(path: str, fields: typing.Sequence[Field], rows: typing.List[list]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    part = path + ".part"
    if os.path.exists(part):
        os.remove(part)
    con = sqlite3.connect(part)
    try:
        columns = ['"zipcode" TEXT PRIMARY KEY NOT NULL'] + ['"%s" %s' % (f.name, SQL_TYPES[f.dtype]) for f in fields]
        con.execute('CREATE TABLE "%s" (%s)' % (TABLE, ", ".join(columns)))
        con.executemany('INSERT INTO "%s" VALUES (%s)' % (TABLE, ", ".join("?" * (len(fields) + 1))), rows)
        con.commit()
    finally:
        con.close()
    replace(part, path)


def build(fields: typing.Sequence[Field], crawlers: typing.Sequence[Crawler], paths: Paths,
          pk_set: str = "demo") -> dict:
    """Validate, load the PK set and the crawler outputs, join and write. Returns the coverage report."""
    require_valid(fields, crawlers, paths.mise_toml)
    name, pks = load_pk_set(pk_set, paths)
    catalog = {f.name: f for f in fields}
    owner = owners(crawlers)
    outputs = {c.name: read_output(c, catalog, paths.crawler_out_dir) for c in crawlers}
    metas = {c.name: read_meta(c, paths.crawler_out_dir) for c in crawlers}
    rows = assemble(pks, fields, owner, outputs)

    stem = os.path.join(paths.db_out_dir, "db_%s" % name)
    _write_sqlite(stem + ".sqlite", fields, rows)
    write_csv(stem + ".csv", ["zipcode"] + [f.name for f in fields], rows)

    pk_index = set(pks)
    field_cov = {}
    for j, f in enumerate(fields, start=1):
        out = outputs[owner[f.name]]
        not_in_source = sum(1 for pk in pks if pk not in out)
        non_null = sum(1 for r in rows if r[j] is not None)
        field_cov[f.name] = {
            "crawler": owner[f.name], "non_null": non_null, "share": round(non_null / len(pks), 4),
            "not_in_source": not_in_source, "empty_in_source": len(pks) - non_null - not_in_source,
        }
    crawler_cov = {}
    for c in crawlers:
        out = outputs[c.name]
        inside = sum(1 for z in out if z in pk_index)
        crawler_cov[c.name] = {
            "source_rows": len(out), "rows_in_pk_set": inside, "rows_outside_pk_set": len(out) - inside,
            "downloads": {fn: {k: e.get(k) for k in ("url", "bytes", "sha256", "fetched_at_utc")}
                          for fn, e in sorted(metas[c.name].get("downloads", {}).items())},
        }
    by_count = {}
    for r in rows:
        n = sum(1 for v in r[1:] if v is not None)
        by_count[str(n)] = by_count.get(str(n), 0) + 1
    coverage = {
        "pk_set": name, "pks": len(pks), "columns": 1 + len(fields),
        "fields": field_cov, "crawlers": crawler_cov,
        "pks_by_non_null_fields": dict(sorted(by_count.items(), key=lambda kv: int(kv[0]))),
        "pks_without_any_value": [r[0] for r in rows if all(v is None for v in r[1:])],
        "files": {"sqlite": stem + ".sqlite", "csv": stem + ".csv"},
    }
    # keys in build order (Fields in catalog order, crawlers in registry order); still deterministic
    write_json(stem + "_coverage.json", dict(coverage, files={k: os.path.basename(v) for k, v in coverage["files"].items()}),
               sort_keys=False)
    return coverage


def describe_coverage(coverage: dict) -> str:
    """The coverage report as a console table."""
    lines = ["PK set %r: %d rows x %d columns" % (coverage["pk_set"], coverage["pks"], coverage["columns"])]
    rows = [("field", "crawler", "values", "share", "not in source", "empty in source")]
    for name, c in coverage["fields"].items():
        rows.append((name, c["crawler"], "%d/%d" % (c["non_null"], coverage["pks"]), "%.1f%%" % (100 * c["share"]),
                     str(c["not_in_source"]), str(c["empty_in_source"])))
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    lines += ["  " + "  ".join(cell.ljust(w) for cell, w in zip(r, widths)).rstrip() for r in rows]
    empty = coverage["pks_without_any_value"]
    if empty:
        shown = ", ".join(empty[:10]) + (" ... (%d in total)" % len(empty) if len(empty) > 10 else "")
        lines.append("PKs without any value (normal for PO box, unique and military ZIPs): " + shown)
    return "\n".join(lines)
