# -*- coding: utf-8 -*-

"""
zip-basics: what identifies a ZIP. No single free source has every ZIP, so this
crawler downloads three files, one source row per ZIP found in any of them:

- HUD-USPS ZIP Code Crosswalk, ZIP to county (about 8 MB, free token read from
  ``$HUD_API_TOKEN`` or ``~/.hud_token``): columns ``hud_city``, ``hud_state``.
- Census ZIP Code Business Patterns totals (about 1 MB): ``zbp_city``, ``zbp_state``.
- the uszipcode 2.x ``simple_db.sqlite`` release (about 11 MB, not a government
  source): ``v2_city``, ``v2_state``, ``v2_zipcode_type``.

A column is absent when that file does not list the ZIP. The Fields decide the
order in which they fall back from one source to the next.
"""

import csv
import io
import json
import sqlite3
import zipfile

from ...zipcodes import normalize_zip
from ..core import Crawler, Download, Secret

HUD_URL = "https://www.huduser.gov/hudapi/public/usps?type=2&query=All"
HUD_FILENAME = "hud_zip_county_all.json"
HUD_TOKEN = Secret(
    env="HUD_API_TOKEN",
    file="~/.hud_token",
    signup_url="https://www.huduser.gov/hudapi/public/register",
    bearer=True,
)
ZBP_URL = "https://www2.census.gov/programs-surveys/cbp/datasets/2023/zbp23totals.zip"
ZBP_FILENAME = "zbp23totals.zip"
V2_URL = "https://github.com/MacHu-GWU/uszipcode-project/releases/download/1.0.1.db/simple_db.sqlite"
V2_FILENAME = "v2_simple_db.sqlite"


def _read_hud(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)["data"]
    for rec in data["results"] if isinstance(data, dict) else data:  # one record per county of the ZIP
        yield rec.get("zip"), {"hud_city": rec.get("city"), "hud_state": rec.get("state")}


def _read_zbp(path):
    with zipfile.ZipFile(path) as z:
        name = [n for n in z.namelist() if n.lower().endswith(".txt")][0]
        text = z.read(name).decode("latin-1")
    for rec in csv.DictReader(io.StringIO(text)):
        yield rec.get("zip"), {"zbp_city": rec.get("city"), "zbp_state": rec.get("stabbr")}


def _read_v2(path):
    con = sqlite3.connect(path)
    try:
        rows = con.execute("SELECT zipcode, zipcode_type, major_city, state FROM simple_zipcode").fetchall()
    finally:
        con.close()
    for zipcode, zipcode_type, city, state in rows:
        yield zipcode, {"v2_zipcode_type": zipcode_type, "v2_city": city, "v2_state": state}


def parse(files):
    rows = {}
    readers = ((_read_hud, HUD_FILENAME), (_read_zbp, ZBP_FILENAME), (_read_v2, V2_FILENAME))
    for read, filename in readers:
        for key, values in read(files[filename]):
            zipcode = normalize_zip(key)
            if zipcode:
                row = rows.setdefault(zipcode, {})
                for name, value in values.items():
                    if value and not row.get(name):
                        row[name] = value
    return iter(rows.items())


CRAWLER = Crawler(
    name="zip-basics",
    fields=("zipcode_type", "major_city", "state"),
    downloads=(
        Download(HUD_FILENAME, HUD_URL, magic=b"{", secret=HUD_TOKEN),
        Download(ZBP_FILENAME, ZBP_URL, magic=b"PK\x03\x04"),
        Download(V2_FILENAME, V2_URL, magic=b"SQLite format 3\x00"),
    ),
    parse=parse,
    description="HUD-USPS crosswalk, Census ZBP, uszipcode 2.x -> zipcode_type, major_city, state",
)
