# -*- coding: utf-8 -*-

"""
Merge the ZIP lists of all sources into one primary-key table.

Usage (from the repository root)::

    python -m data_pipeline.zipcode_universe                 # all sources, including the 2.x list
    python -m data_pipeline.zipcode_universe --no-v2         # government sources only
    python -m data_pipeline.zipcode_universe --irs-years 2011-2022

Output: ``data_pipeline/output/zipcode_universe.csv`` (one row per ZIP) and
``zipcode_universe_summary.json`` (counts per source and coverage of the 2.x list).
"""

import argparse
import collections
import csv
import datetime
import json
import os
import sys
import typing

from .sources import SOURCES, Records, is_military_zip

HERE = os.path.dirname(os.path.abspath(__file__))
PIPELINE_DIR = os.path.dirname(HERE)
DEFAULT_CACHE_DIR = os.path.join(PIPELINE_DIR, ".cache", "zipcode_universe")
DEFAULT_OUT = os.path.join(PIPELINE_DIR, "output", "zipcode_universe.csv")
DEFAULT_SUMMARY = os.path.join(PIPELINE_DIR, "output", "zipcode_universe_summary.json")

#: order of preference when sources disagree on the city / state
CITY_PRIORITY = ("hud", "zbp", "v2")
STATE_PRIORITY = ("hud", "zbp", "irs", "v2")

COLUMNS = [
    "zipcode", "city", "state", "city_source",
    "in_census_zcta", "in_hud", "in_zbp", "in_irs", "in_v2", "n_gov_sources",
    "is_military_prefix",
    "hud_has_residential", "hud_has_business", "hud_has_other", "hud_county_count",
    "irs_years", "v2_zipcode_type",
]


def merge(records: typing.Dict[str, Records]) -> typing.List[dict]:
    """
    ``records`` maps a source name to its ``{zipcode: attributes}``. Returns one row
    per ZIP found in any source, sorted by ZIP.
    """
    gov = [name for name in records if SOURCES.get(name, (None, True))[1]]
    rows = []
    for z in sorted(set().union(*[set(r) for r in records.values()])):
        row = {c: None for c in COLUMNS}
        row["zipcode"] = z
        for name in ("census_zcta", "hud", "zbp", "irs", "v2"):
            row["in_" + name] = int(z in records.get(name, {}))
        row["n_gov_sources"] = sum(1 for name in gov if z in records[name])
        row["is_military_prefix"] = int(is_military_zip(z))
        for name in CITY_PRIORITY:
            city = records.get(name, {}).get(z, {}).get("city")
            if city:
                row["city"], row["city_source"] = city.strip().upper(), name
                break
        for name in STATE_PRIORITY:
            state = records.get(name, {}).get(z, {}).get("state")
            if state:
                row["state"] = state.strip().upper()
                break
        hud = records.get("hud", {}).get(z)
        if hud:
            for k in ("hud_has_residential", "hud_has_business", "hud_has_other"):
                row[k] = int(bool(hud[k]))
            row["hud_county_count"] = hud["hud_county_count"]
        irs = records.get("irs", {}).get(z)
        if irs:
            row["irs_years"] = ";".join(str(y) for y in irs["irs_years"])
        v2 = records.get("v2", {}).get(z)
        if v2:
            row["v2_zipcode_type"] = v2["v2_zipcode_type"]
        rows.append(row)
    return rows


def write_csv(rows: typing.List[dict], path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: ("" if v is None else v) for k, v in row.items()})


def summarize(rows: typing.List[dict], records: typing.Dict[str, Records], params: dict) -> dict:
    by_type = collections.Counter(r["v2_zipcode_type"] for r in rows if r["in_v2"])
    covered = collections.Counter(r["v2_zipcode_type"] for r in rows if r["in_v2"] and r["n_gov_sources"] > 0)
    return {
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
        "parameters": params,
        "zip_codes_total": len(rows),
        "zip_codes_in_any_government_source": sum(1 for r in rows if r["n_gov_sources"] > 0),
        "zip_codes_only_in_v2": sum(1 for r in rows if r["in_v2"] and r["n_gov_sources"] == 0),
        "zip_codes_per_source": {name: len(rec) for name, rec in records.items()},
        "zip_codes_in_military_prefixes": sum(r["is_military_prefix"] for r in rows),
        "zip_codes_without_city": sum(1 for r in rows if not r["city"]),
        "v2_coverage_by_type": {
            t: {"in_v2": n, "in_a_government_source": covered.get(t, 0),
                "share": round(covered.get(t, 0) / n, 4) if n else None}
            for t, n in by_type.most_common()
        },
        "not_in_v2": sorted(r["zipcode"] for r in rows if not r["in_v2"]),
    }


def _parse_years(text: str) -> typing.List[int]:
    years = []
    for part in text.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            years.extend(range(int(a), int(b) + 1))
        elif part:
            years.append(int(part))
    return years


def main(argv: typing.Optional[typing.List[str]] = None) -> dict:
    p = argparse.ArgumentParser(prog="python -m data_pipeline.zipcode_universe", description=__doc__.split("\n\n")[0])
    p.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR, help="where downloads are kept (default: %(default)s)")
    p.add_argument("--out", default=DEFAULT_OUT, help="CSV output (default: %(default)s)")
    p.add_argument("--summary", default=DEFAULT_SUMMARY, help="JSON summary output (default: %(default)s)")
    p.add_argument("--zbp-year", type=int, default=2023, help="ZIP Code Business Patterns year (default: %(default)s)")
    p.add_argument("--irs-years", default="2022", help="IRS tax years, e.g. 2022 or 2011-2022 (default: %(default)s)")
    p.add_argument("--no-v2", action="store_true", help="leave out the 2.x list (government sources only)")
    p.add_argument("--hud-token-file", default=None, help="file with the HUD API token (default: ~/.hud_token or $HUD_API_TOKEN)")
    args = p.parse_args(argv)

    options = {"zbp_year": args.zbp_year, "irs_years": _parse_years(args.irs_years), "hud_token_file": args.hud_token_file}
    names = [n for n in SOURCES if not (args.no_v2 and n == "v2")]
    records = {}
    for name in names:
        loader, _ = SOURCES[name]
        print("loading %-12s ..." % name, end=" ", flush=True)
        records[name] = loader(args.cache_dir, **options)
        print("%d ZIP codes" % len(records[name]), flush=True)

    rows = merge(records)
    write_csv(rows, args.out)
    params = {"sources": names, "zbp_year": args.zbp_year, "irs_years": options["irs_years"]}
    summary = summarize(rows, records, params)
    os.makedirs(os.path.dirname(os.path.abspath(args.summary)), exist_ok=True)
    with open(args.summary, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, indent=2)
        fh.write("\n")

    print("total ZIP codes: %d (in a government source: %d, only in the 2.x list: %d)" % (
        summary["zip_codes_total"], summary["zip_codes_in_any_government_source"], summary["zip_codes_only_in_v2"]))
    for t, c in summary["v2_coverage_by_type"].items():
        print("  2.x %-9s %6d, of which in a government source %6d (%.1f%%)" % (
            t, c["in_v2"], c["in_a_government_source"], 100 * (c["share"] or 0)))
    print("wrote", os.path.relpath(args.out), "and", os.path.relpath(args.summary))
    return summary


if __name__ == "__main__":
    main(sys.argv[1:])
