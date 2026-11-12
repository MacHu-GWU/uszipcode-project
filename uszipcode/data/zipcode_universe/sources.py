# -*- coding: utf-8 -*-

"""
Free sources of 5-digit ZIP codes.

Each source has a ``parse_*`` function that turns the raw file into
``{zipcode: {attribute: value}}`` (no network, easy to test) and a ``load_*``
function that gets the file and parses it. The files are downloaded by
``fetch.py``, like those of the crawlers: once, into ``<cache>/zipcode_universe/``,
with its retries, its resumed downloads and its check of the first bytes.

==============  ================================================  ===================================
source          what it is                                        what it misses
==============  ================================================  ===================================
census_zcta     Census ZIP Code Tabulation Areas (2020 ZCTAs,     PO-box-only, unique and military
                2025 Gazetteer)                                   ZIPs (no polygon)
hud             HUD-USPS ZIP Code Crosswalk, ZIP to county        ZIPs that only serve PO boxes,
                (USPS address data, updated quarterly)            military ZIPs
zbp             Census ZIP Code Business Patterns totals          ZIPs without business
                                                                  establishments
irs             IRS SOI ZIP Code Data (tax returns)               ZIPs with fewer than 100 returns,
                                                                  APO/FPO addresses
v2              the uszipcode 2.x ``simple_db.sqlite`` release    not a government source; frozen
                (legacy list, 42,724 ZIPs with a ZIP type)        at the 2.x build
==============  ================================================  ===================================
"""

import csv
import dataclasses
import io
import json
import sqlite3
import typing
import zipfile

from .. import fetch
from ..core import Crawler, Download
from ..keys import HUD_TOKEN
from ..zipcodes import normalize_zip

#: the folder of these downloads inside the cache folder
CACHE_NAME = "zipcode_universe"
ZIP_MAGIC = b"PK\x03\x04"

GAZETTEER_ZCTA_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
    "2025_Gazetteer/2025_Gaz_zcta_national.zip"
)
HUD_ZIP_COUNTY_URL = "https://www.huduser.gov/hudapi/public/usps?type=2&query=All"
ZBP_TOTALS_URL = "https://www2.census.gov/programs-surveys/cbp/datasets/{year}/zbp{yy:02d}totals.zip"
IRS_ZIP_URL = "https://www.irs.gov/pub/irs-soi/{yy:02d}zpallnoagi.csv"
V2_SIMPLE_DB_URL = (
    "https://github.com/MacHu-GWU/uszipcode-project/releases/download/"
    "1.0.1.db/simple_db.sqlite"
)

#: 3-digit prefixes reserved for APO / FPO / DPO (military and diplomatic) mail:
#: AE 090-099, AA 340, AP 962-966.
MILITARY_PREFIXES = frozenset(
    ["%03d" % p for p in range(90, 100)] + ["340"] + [str(p) for p in range(962, 967)]
)

Records = typing.Dict[str, typing.Dict[str, typing.Any]]


def is_military_zip(zipcode: str) -> bool:
    """True if the ZIP falls in the APO / FPO / DPO prefix ranges."""
    return zipcode[:3] in MILITARY_PREFIXES


# ------------------------------------------------------------------------------------------ download
def download(cache_dir: str, *downloads: Download) -> typing.List[str]:
    """
    The local paths of ``downloads``, in order. ``fetch.py`` fetches those that are
    not yet in ``<cache_dir>/zipcode_universe/`` and keeps a manifest there.
    """
    source = Crawler(CACHE_NAME, (), tuple(downloads), parse=lambda files: ())
    files, _ = fetch.fetch_all(source, cache_dir)
    return [files[d.filename] for d in downloads]


def _zip_member_text(path: str, suffix: str, encoding: str) -> str:
    with zipfile.ZipFile(path) as z:
        name = [n for n in z.namelist() if n.lower().endswith(suffix)][0]
        return z.read(name).decode(encoding)


# ------------------------------------------------------------------------------------------ parsers
def parse_gazetteer(text: str) -> Records:
    """Census Gazetteer ZCTA file (pipe-delimited, column ``GEOID``)."""
    reader = csv.reader(io.StringIO(text), delimiter="|")
    header = [h.strip() for h in next(reader)]
    i = header.index("GEOID")
    out = {}
    for row in reader:
        z = normalize_zip(row[i]) if len(row) > i else None
        if z:
            out[z] = {}
    return out


def parse_hud(payload: dict) -> Records:
    """
    HUD-USPS crosswalk type 2 (ZIP to county), all records. A ZIP has one record
    per county; the address shares are combined into "does it have any
    residential / business / other addresses".
    """
    data = payload["data"]
    results = data["results"] if isinstance(data, dict) else data
    out = {}
    for rec in results:
        z = normalize_zip(rec.get("zip"))
        if not z:
            continue
        r = out.setdefault(z, {"city": None, "state": None, "hud_has_residential": False,
                               "hud_has_business": False, "hud_has_other": False, "hud_county_count": 0})
        r["city"] = r["city"] or (rec.get("city") or None)
        r["state"] = r["state"] or (rec.get("state") or None)
        r["hud_has_residential"] |= float(rec.get("res_ratio") or 0) > 0
        r["hud_has_business"] |= float(rec.get("bus_ratio") or 0) > 0
        r["hud_has_other"] |= float(rec.get("oth_ratio") or 0) > 0
        r["hud_county_count"] += 1
    return out


def parse_zbp(text: str) -> Records:
    """Census ZIP Code Business Patterns totals file (CSV with ``zip``, ``city``, ``stabbr``)."""
    out = {}
    for row in csv.DictReader(io.StringIO(text)):
        z = normalize_zip(row.get("zip"))
        if z:
            out[z] = {"city": (row.get("city") or "").strip() or None,
                      "state": (row.get("stabbr") or "").strip() or None}
    return out


def parse_irs(text: str) -> Records:
    """IRS SOI ZIP Code Data CSV. The header case differs between years (``zipcode`` / ``ZIPCODE``)."""
    reader = csv.reader(io.StringIO(text))
    header = [h.strip().upper() for h in next(reader)]
    iz, ist = header.index("ZIPCODE"), header.index("STATE")
    out = {}
    for row in reader:
        if len(row) <= max(iz, ist):
            continue
        z = normalize_zip(row[iz])
        if z:
            out[z] = {"state": row[ist].strip() or None}
    return out


def parse_v2(db_path: str) -> Records:
    """The 2.x ``simple_db.sqlite`` release: ZIP, type, city and state."""
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute("SELECT zipcode, zipcode_type, major_city, state FROM simple_zipcode").fetchall()
    finally:
        con.close()
    out = {}
    for z, ztype, city, state in rows:
        z = normalize_zip(z)
        if z:
            out[z] = {"v2_zipcode_type": ztype, "city": city, "state": state}
    return out


# ------------------------------------------------------------------------------------------ loaders
def load_census_zcta(cache_dir: str, **_) -> Records:
    path, = download(cache_dir, Download("2025_Gaz_zcta_national.zip", GAZETTEER_ZCTA_URL, magic=ZIP_MAGIC))
    return parse_gazetteer(_zip_member_text(path, ".txt", "utf-8"))


def load_hud(cache_dir: str, hud_token_file: typing.Optional[str] = None, **_) -> Records:
    """The token is read from ``$HUD_API_TOKEN``, else from ``hud_token_file`` (default ``~/.hud_token``)."""
    token = dataclasses.replace(HUD_TOKEN, file=hud_token_file) if hud_token_file else HUD_TOKEN
    path, = download(cache_dir, Download("hud_zip_county_all.json", HUD_ZIP_COUNTY_URL, magic=b"{", secret=token))
    with open(path, encoding="utf-8") as fh:
        return parse_hud(json.load(fh))


def load_zbp(cache_dir: str, zbp_year: int = 2023, **_) -> Records:
    url = ZBP_TOTALS_URL.format(year=zbp_year, yy=zbp_year % 100)
    path, = download(cache_dir, Download("zbp%02dtotals.zip" % (zbp_year % 100), url, magic=ZIP_MAGIC))
    return parse_zbp(_zip_member_text(path, ".txt", "latin-1"))


def load_irs(cache_dir: str, irs_years: typing.Iterable[int] = (2022,), **_) -> Records:
    out = {}
    years = sorted(irs_years)
    paths = download(cache_dir, *[Download("%02dzpallnoagi.csv" % (year % 100), IRS_ZIP_URL.format(yy=year % 100),
                                           magic=b"STATEFIPS,") for year in years])
    for year, path in zip(years, paths):
        with open(path, encoding="utf-8", errors="replace") as fh:
            for z, attrs in parse_irs(fh.read()).items():
                rec = out.setdefault(z, {"state": attrs["state"], "irs_years": []})
                rec["irs_years"].append(year)
    return out


def load_v2(cache_dir: str, **_) -> Records:
    path, = download(cache_dir, Download("v2_simple_db.sqlite", V2_SIMPLE_DB_URL, magic=b"SQLite format 3\x00"))
    return parse_v2(path)


#: name -> (loader, is a government source)
SOURCES = {
    "census_zcta": (load_census_zcta, True),
    "hud": (load_hud, True),
    "zbp": (load_zbp, True),
    "irs": (load_irs, True),
    "v2": (load_v2, False),
}
