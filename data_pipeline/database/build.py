# -*- coding: utf-8 -*-

"""
Build the database: the PK set LEFT JOIN every crawler output.

Rows are the PKs, columns are ``zipcode`` plus every Field in catalog order, and
NULL means "no value" (normal: a PO box ZIP has no Census statistics). Building
never downloads anything, so switching PK sets is free.

Outputs in ``output/``: ``db_<set>.sqlite`` (table ``zipcode_data``),
``db_<set>.csv`` (the same table) and ``db_<set>_coverage.json``. When there are
history crawlers, the SQLite file also has the table ``zipcode_history`` (one row
per PK and year, columns ``zipcode``, ``year`` and the history Fields), also
written to ``db_<set>_history.csv``.
"""

import csv
import os
import re
import sqlite3
import typing

from ..zipcodes import normalize_zip
from .checks import owners, require_valid
from .core import ContractError, Crawler, Field, Paths, PkSetError, SQL_TYPES, format_problems
from .crawl import coerce, read_meta, read_output, replace, write_csv, write_json

#: the minimal example: two standard ZIPs and a PO box ZIP without a ZCTA (so no Census values)
DEMO_PKS = ("10001", "20013", "20037")
TABLE = "zipcode_data"
HISTORY_TABLE = "zipcode_history"
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


def _join(keys: typing.Sequence, n_key: int, fields: typing.Sequence[Field], owner: typing.Dict[str, str],
          outputs: typing.Dict[str, dict]) -> typing.List[list]:
    """One row per key, ``key + [value per Field]``; one lookup per crawler and key (this runs per cell)."""
    plan = {}
    for j, f in enumerate(fields, start=n_key):
        if f.name in owner:
            plan.setdefault(owner[f.name], []).append((j, f.name))
    plan = [(outputs[name], columns) for name, columns in plan.items()]
    width = n_key + len(fields)
    rows = []
    for key in keys:
        row = [None] * width
        row[:n_key] = key if n_key > 1 else (key,)
        for out, columns in plan:
            record = out.get(key)
            if record is not None:
                for j, name in columns:
                    row[j] = record[name]
        rows.append(row)
    return rows


def assemble(pks: typing.Sequence[str], fields: typing.Sequence[Field], owner: typing.Dict[str, str],
             outputs: typing.Dict[str, typing.Dict[str, dict]]) -> typing.List[list]:
    """Pure left join: one row per PK, ``[zipcode] + [value per Field]``. Derived Fields are None here."""
    return _join(pks, 1, fields, owner, outputs)


def derive(rows: typing.List[list], fields: typing.Sequence[Field]) -> None:
    """Fill in the derived Fields of every row, in catalog order (B4: a derived value fails)."""
    column = {f.name: j for j, f in enumerate(fields, start=1)}
    problems = []
    for j, f in enumerate(fields, start=1):
        if not f.inputs:
            continue
        for row in rows:
            try:
                value, error = coerce(f, f.extract({name: row[column[name]] for name in f.inputs}))
            except Exception as e:
                value, error = None, ("B4", "%s: %s" % (type(e).__name__, e))
            if error:
                problems.append("[B4] derived Field %s, zipcode %s: %s" % (f.name, row[0], error[1]))
            row[j] = value
    if problems:
        raise ContractError(format_problems("derived Fields failed", problems, limit=20))


def assemble_history(pk_index: typing.Set[str], fields: typing.Sequence[Field], owner: typing.Dict[str, str],
                     outputs: typing.Dict[str, typing.Dict[tuple, dict]]) -> typing.List[list]:
    """
    The history table: one row per (zipcode, year) that a history crawler has for a PK,
    ``[zipcode, year] + [value per history Field]``, sorted.
    """
    keys = sorted({key for out in outputs.values() for key in out if key[0] in pk_index})
    return _join(keys, 2, fields, owner, outputs)


def _create_table(con, table: str, key: typing.List[str], fields: typing.Sequence[Field], rows: typing.List[list],
                  constraints: typing.Sequence[str] = ()) -> None:
    columns = key + ['"%s" %s' % (f.name, SQL_TYPES[f.dtype]) for f in fields] + list(constraints)
    con.execute('CREATE TABLE "%s" (%s)' % (table, ", ".join(columns)))
    con.executemany('INSERT INTO "%s" VALUES (%s)' % (table, ", ".join("?" * (len(fields) + len(key)))), rows)


def _write_sqlite(path: str, fields: typing.Sequence[Field], rows: typing.List[list],
                  history_fields: typing.Sequence[Field] = (), history_rows: typing.Optional[typing.List[list]] = None) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    part = path + ".part"
    if os.path.exists(part):
        os.remove(part)
    con = sqlite3.connect(part)
    try:
        _create_table(con, TABLE, ['"zipcode" TEXT PRIMARY KEY NOT NULL'], fields, rows)
        if history_rows is not None:
            _create_table(con, HISTORY_TABLE, ['"zipcode" TEXT NOT NULL', '"year" INTEGER NOT NULL'], history_fields,
                          history_rows, constraints=['PRIMARY KEY ("zipcode", "year")'])
        con.commit()
    finally:
        con.close()
    replace(part, path)


def _downloads(meta: dict) -> dict:
    return {fn: {k: e.get(k) for k in ("url", "bytes", "sha256", "fetched_at_utc")}
            for fn, e in sorted(meta.get("downloads", {}).items())}


def _crawler_coverage(out: dict, pk_index: typing.Set[str], meta: dict) -> dict:
    inside = sum(1 for key in out if (key[0] if isinstance(key, tuple) else key) in pk_index)
    return {"source_rows": len(out), "rows_in_pk_set": inside, "rows_outside_pk_set": len(out) - inside,
            "downloads": _downloads(meta)}


def _history_coverage(fields: typing.Sequence[Field], crawlers: typing.Sequence[Crawler], owner: typing.Dict[str, str],
                      outputs: dict, rows: typing.List[list], pk_index: typing.Set[str], metas: dict) -> dict:
    field_cov = {}
    columns = list(zip(*rows)) if rows else [()] * (2 + len(fields))
    for j, f in enumerate(fields, start=2):
        field_cov[f.name] = {"crawler": owner[f.name], "non_null": len(rows) - columns[j].count(None),
                             "years": sorted({y for y, v in zip(columns[1], columns[j]) if v is not None})}
    return {
        "table": HISTORY_TABLE, "rows": len(rows), "pks": len({r[0] for r in rows}),
        "columns": 2 + len(fields), "years": sorted({r[1] for r in rows}),
        "fields": field_cov,
        "crawlers": {c.name: _crawler_coverage(outputs[c.name], pk_index, metas[c.name]) for c in crawlers},
    }


def build(fields: typing.Sequence[Field], crawlers: typing.Sequence[Crawler], paths: Paths,
          pk_set: str = "demo", history_fields: typing.Sequence[Field] = ()) -> dict:
    """Validate, load the PK set and the crawler outputs, join and write. Returns the coverage report."""
    require_valid(fields, crawlers, paths.mise_toml, history_fields)
    name, pks = load_pk_set(pk_set, paths)
    pk_index = set(pks)
    main = [c for c in crawlers if not c.history]
    history = [c for c in crawlers if c.history]
    catalog = {f.name: f for f in fields}
    owner = owners(main)
    outputs = {c.name: read_output(c, catalog, paths.crawler_out_dir) for c in main}
    metas = {c.name: read_meta(c, paths.crawler_out_dir) for c in crawlers}
    rows = assemble(pks, fields, owner, outputs)
    derive(rows, fields)
    history_rows = None
    if history:
        history_catalog = {f.name: f for f in history_fields}
        history_owner = owners(history)
        history_outputs = {c.name: read_output(c, history_catalog, paths.crawler_out_dir) for c in history}
        history_rows = assemble_history(pk_index, history_fields, history_owner, history_outputs)

    stem = os.path.join(paths.db_out_dir, "db_%s" % name)
    files = {"sqlite": stem + ".sqlite", "csv": stem + ".csv"}
    _write_sqlite(files["sqlite"], fields, rows, history_fields, history_rows)
    write_csv(files["csv"], ["zipcode"] + [f.name for f in fields], rows)
    if history_rows is not None:
        files["history_csv"] = stem + "_history.csv"
        write_csv(files["history_csv"], ["zipcode", "year"] + [f.name for f in history_fields], history_rows)

    column = {f.name: j for j, f in enumerate(fields, start=1)}
    columns = list(zip(*rows))  # counted with list.count, which runs in C
    missing = {c.name: sum(1 for pk in pks if pk not in outputs[c.name]) for c in main}
    field_cov = {}
    for j, f in enumerate(fields, start=1):
        non_null = len(rows) - columns[j].count(None)
        if f.inputs:  # "not in source": an input is NULL
            inputs = [column[n] for n in f.inputs]
            not_in_source = sum(1 for r in rows if any(r[i] is None for i in inputs))
        else:
            not_in_source = missing[owner[f.name]]
        field_cov[f.name] = {
            "crawler": "derived" if f.inputs else owner[f.name], "non_null": non_null,
            "share": round(non_null / len(pks), 4),
            "not_in_source": not_in_source, "empty_in_source": len(pks) - non_null - not_in_source,
        }
        if f.inputs:
            field_cov[f.name]["derived_from"] = list(f.inputs)
    crawler_cov = {c.name: _crawler_coverage(outputs[c.name], pk_index, metas[c.name]) for c in main}
    by_count = {}
    for r in rows:
        n = len(r) - 1 - r.count(None)
        by_count[str(n)] = by_count.get(str(n), 0) + 1
    coverage = {
        "pk_set": name, "pks": len(pks), "columns": 1 + len(fields),
        "fields": field_cov, "crawlers": crawler_cov,
        "pks_by_non_null_fields": dict(sorted(by_count.items(), key=lambda kv: int(kv[0]))),
        "pks_without_any_value": [r[0] for r in rows if r.count(None) == len(r) - 1],
    }
    if history_rows is not None:
        coverage["history"] = _history_coverage(history_fields, history, history_owner, history_outputs,
                                                history_rows, pk_index, metas)
    coverage["files"] = files
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
    history = coverage.get("history")
    if history:
        years = history["years"]
        lines.append("History table %s: %d rows (zipcode x year) for %d PKs, years %s" % (
            history["table"], history["rows"], history["pks"], "%d-%d" % (years[0], years[-1]) if years else "none"))
        rows = [("field", "crawler", "values", "years")]
        for name, c in history["fields"].items():
            span = c["years"]
            rows.append((name, c["crawler"], str(c["non_null"]),
                         "%d-%d (%d)" % (span[0], span[-1], len(span)) if span else "-"))
        widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
        lines += ["  " + "  ".join(cell.ljust(w) for cell, w in zip(r, widths)).rstrip() for r in rows]
    return "\n".join(lines)
