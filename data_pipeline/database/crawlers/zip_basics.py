# -*- coding: utf-8 -*-

"""
zip-basics: what identifies a ZIP. No single free source has every ZIP, so this
crawler downloads four files, one source row per ZIP found in any of them:

- HUD-USPS ZIP Code Crosswalk, ZIP to county (about 8 MB, free token read from
  ``$HUD_API_TOKEN`` or ``~/.hud_token``): columns ``hud_city``, ``hud_state``, and
  ``hud_county_fips``, ``hud_county_name`` for the ZIP's main county.
- Census Gazetteer counties file (about 0.1 MB): only the county names for the above.
- Census ZIP Code Business Patterns totals (about 1 MB): ``zbp_city``, ``zbp_state``.
- the uszipcode 2.x ``simple_db.sqlite`` release (about 11 MB, not a government
  source): ``v2_city``, ``v2_state``, ``v2_county``, ``v2_zipcode_type``.

A column is absent when that file does not list the ZIP. The Fields decide the
order in which they fall back from one source to the next.

A ZIP has one HUD record per county it spans (about 29% span more than one). The
main county is the one with the largest share of the ZIP's residential addresses,
then of all its addresses, then the lowest county code.
"""

import csv
import io
import json
import sqlite3
import zipfile

from ...zipcodes import normalize_zip
from ..core import Crawler, Download, Secret, field_names
from ..fields import zipcode_type, major_city, state, county, county_fips

HUD_URL = "https://www.huduser.gov/hudapi/public/usps?type=2&query=All"
HUD_FILENAME = "hud_zip_county_all.json"
HUD_TOKEN = Secret(
    env="HUD_API_TOKEN",
    file="~/.hud_token",
    signup_url="https://www.huduser.gov/hudapi/public/register",
    bearer=True,
)
COUNTIES_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
    "2025_Gazetteer/2025_Gaz_counties_national.zip"
)
COUNTIES_FILENAME = "2025_Gaz_counties_national.zip"
ZBP_URL = "https://www2.census.gov/programs-surveys/cbp/datasets/2023/zbp23totals.zip"
ZBP_FILENAME = "zbp23totals.zip"
V2_URL = "https://github.com/MacHu-GWU/uszipcode-project/releases/download/1.0.1.db/simple_db.sqlite"
V2_FILENAME = "v2_simple_db.sqlite"


def _zip_text(path: str, encoding: str) -> str:
    with zipfile.ZipFile(path) as z:
        name = [n for n in z.namelist() if n.lower().endswith(".txt")][0]
        return z.read(name).decode(encoding)


def _county_names(path):
    """GEOID -> NAME from the Gazetteer counties file (pipe- or tab-delimited, depending on the year)."""
    text = _zip_text(path, "utf-8")
    delimiter = "|" if "|" in text.split("\n", 1)[0] else "\t"
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    header = [h.strip() for h in next(reader)]
    i_geoid, i_name = header.index("GEOID"), header.index("NAME")
    return {row[i_geoid].strip(): row[i_name].strip() for row in reader if len(row) > i_name}


def _read_hud(path, county_names):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)["data"]
    by_zip = {}
    for rec in data["results"] if isinstance(data, dict) else data:  # one record per county of the ZIP
        by_zip.setdefault(rec.get("zip"), []).append(rec)
    for key, records in by_zip.items():
        main = min(records, key=lambda r: (-float(r.get("res_ratio") or 0), -float(r.get("tot_ratio") or 0),
                                           str(r.get("geoid"))))
        city = next((r.get("city") for r in records if r.get("city")), None)
        state = next((r.get("state") for r in records if r.get("state")), None)
        fips = str(main.get("geoid") or "")
        yield key, {"hud_city": city, "hud_state": state, "hud_county_fips": fips,
                    "hud_county_name": county_names.get(fips)}


def _read_zbp(path):
    for rec in csv.DictReader(io.StringIO(_zip_text(path, "latin-1"))):
        yield rec.get("zip"), {"zbp_city": rec.get("city"), "zbp_state": rec.get("stabbr")}


def _read_v2(path):
    con = sqlite3.connect(path)
    try:
        rows = con.execute("SELECT zipcode, zipcode_type, major_city, county, state FROM simple_zipcode").fetchall()
    finally:
        con.close()
    for zipcode, zipcode_type, city, county, state in rows:
        yield zipcode, {"v2_zipcode_type": zipcode_type, "v2_city": city, "v2_county": county, "v2_state": state}


def parse(files):
    rows = {}
    county_names = _county_names(files[COUNTIES_FILENAME])
    sources = (_read_hud(files[HUD_FILENAME], county_names), _read_zbp(files[ZBP_FILENAME]),
               _read_v2(files[V2_FILENAME]))
    for source in sources:
        for key, values in source:
            zipcode = normalize_zip(key)
            if zipcode:
                row = rows.setdefault(zipcode, {})
                for name, value in values.items():
                    if value and not row.get(name):
                        row[name] = value
    return iter(rows.items())


CRAWLER = Crawler(
    name="zip-basics",
    fields=field_names(zipcode_type, major_city, state, county, county_fips),
    downloads=(
        Download(HUD_FILENAME, HUD_URL, magic=b"{", secret=HUD_TOKEN),
        Download(COUNTIES_FILENAME, COUNTIES_URL, magic=b"PK\x03\x04"),
        Download(ZBP_FILENAME, ZBP_URL, magic=b"PK\x03\x04"),
        Download(V2_FILENAME, V2_URL, magic=b"SQLite format 3\x00"),
    ),
    parse=parse,
    description="HUD-USPS crosswalk, Census Gazetteer counties, Census ZBP, uszipcode 2.x -> ZIP type, city, state, county",
)
