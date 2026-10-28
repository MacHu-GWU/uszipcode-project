# -*- coding: utf-8 -*-

"""
Free sources of 5-digit ZIP codes.

Each source has a ``parse_*`` function that turns the raw file into
``{zipcode: {attribute: value}}`` (no network, easy to test) and a ``load_*``
function that downloads the file into a cache folder and parses it.

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
import io
import json
import os
import sqlite3
import time
import typing
import urllib.error
import urllib.request
import zipfile

USER_AGENT = "uszipcode-data-pipeline"

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


def normalize_zip(value) -> typing.Optional[str]:
    """
    Return the 5-digit ZIP as a string with leading zeros, or None if ``value``
    is not a ZIP code. ``"501"`` -> ``"00501"``; ``"00000"``, ``"99999"``
    (used as totals / "other" in some files) and non-digits -> None.
    """
    if value is None:
        return None
    s = str(value).strip()
    if s.endswith(".0"):  # numbers read from spreadsheets
        s = s[:-2]
    if not s.isdigit() or len(s) > 5:
        return None
    s = s.zfill(5)
    if s in ("00000", "99999"):
        return None
    return s


def is_military_zip(zipcode: str) -> bool:
    """True if the ZIP falls in the APO / FPO / DPO prefix ranges."""
    return zipcode[:3] in MILITARY_PREFIXES


# ------------------------------------------------------------------------------------------ download
def download(url: str, dest: str, headers: typing.Optional[dict] = None,
             attempts: int = 6, timeout: int = 300) -> str:
    """
    Download ``url`` to ``dest`` unless ``dest`` already exists. Retries from the
    start on failure (the IRS server sometimes closes the connection mid-file).
    """
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    part = dest + ".part"
    req_headers = {"User-Agent": USER_AGENT}
    req_headers.update(headers or {})
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers=req_headers)
            with urllib.request.urlopen(request, timeout=timeout) as response, open(part, "wb") as fh:
                while True:
                    chunk = response.read(1 << 20)
                    if not chunk:
                        break
                    fh.write(chunk)
            os.replace(part, dest)
            return dest
        except urllib.error.HTTPError as e:
            last_error = "HTTP %s" % e.code
            if e.code in (401, 403, 404):
                break
        except (urllib.error.URLError, OSError) as e:
            last_error = type(e).__name__
        if os.path.exists(part):
            os.remove(part)
        time.sleep(3 * attempt)
    raise RuntimeError("download failed (%s): %s" % (last_error, url.split("?")[0]))


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
    path = download(GAZETTEER_ZCTA_URL, os.path.join(cache_dir, "2025_Gaz_zcta_national.zip"))
    return parse_gazetteer(_zip_member_text(path, ".txt", "utf-8"))


def read_hud_token(token_file: typing.Optional[str] = None) -> str:
    """The HUD API token, from ``$HUD_API_TOKEN`` or a file (default ``~/.hud_token``)."""
    token = os.environ.get("HUD_API_TOKEN")
    if token:
        return token.strip()
    path = os.path.expanduser(token_file or "~/.hud_token")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return fh.read().strip()
    raise RuntimeError(
        "no HUD API token: set HUD_API_TOKEN or save the token in ~/.hud_token "
        "(free account at https://www.huduser.gov/hudapi/public/register, dataset 'USPS Crosswalk')"
    )


def load_hud(cache_dir: str, hud_token_file: typing.Optional[str] = None, **_) -> Records:
    path = os.path.join(cache_dir, "hud_zip_county_all.json")
    if not os.path.exists(path):
        token = read_hud_token(hud_token_file)
        download(HUD_ZIP_COUNTY_URL, path,
                 headers={"Authorization": "Bearer " + token, "Accept": "application/json"})
    with open(path, encoding="utf-8") as fh:
        return parse_hud(json.load(fh))


def load_zbp(cache_dir: str, zbp_year: int = 2023, **_) -> Records:
    url = ZBP_TOTALS_URL.format(year=zbp_year, yy=zbp_year % 100)
    path = download(url, os.path.join(cache_dir, "zbp%02dtotals.zip" % (zbp_year % 100)))
    return parse_zbp(_zip_member_text(path, ".txt", "latin-1"))


def load_irs(cache_dir: str, irs_years: typing.Iterable[int] = (2022,), **_) -> Records:
    out = {}
    for year in sorted(irs_years):
        url = IRS_ZIP_URL.format(yy=year % 100)
        path = download(url, os.path.join(cache_dir, "%02dzpallnoagi.csv" % (year % 100)))
        with open(path, encoding="utf-8", errors="replace") as fh:
            for z, attrs in parse_irs(fh.read()).items():
                rec = out.setdefault(z, {"state": attrs["state"], "irs_years": []})
                rec["irs_years"].append(year)
    return out


def load_v2(cache_dir: str, **_) -> Records:
    path = download(V2_SIMPLE_DB_URL, os.path.join(cache_dir, "v2_simple_db.sqlite"))
    return parse_v2(path)


#: name -> (loader, is a government source)
SOURCES = {
    "census_zcta": (load_census_zcta, True),
    "hud": (load_hud, True),
    "zbp": (load_zbp, True),
    "irs": (load_irs, True),
    "v2": (load_v2, False),
}
