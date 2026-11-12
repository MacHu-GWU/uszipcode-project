# -*- coding: utf-8 -*-

"""
zip-basics: what identifies a ZIP and where it is. No single free source has every
ZIP, so this crawler downloads six files, one source row per ZIP found in any of the
first four:

- HUD-USPS ZIP Code Crosswalk, ZIP to county (about 8 MB, free token read from
  ``$HUD_API_TOKEN`` or ``~/.hud_token``): columns ``hud_city``, ``hud_state``,
  ``hud_county_fips``, ``hud_county_name`` for the ZIP's main county, and
  ``hud_counties``, all its counties as JSON text.
- Census ZIP Code Business Patterns totals (about 1 MB): ``zbp_city``, ``zbp_state``.
- the uszipcode 2.x ``simple_db.sqlite`` release (about 11 MB, not a government
  source): ``v2_city``, ``v2_state``, ``v2_county``, ``v2_zipcode_type``.
- Census Gazetteer ZCTA file (about 1 MB), one line per ZCTA, under its own header:
  ``GEOID|GEOIDFQ|ALAND|AWATER|ALAND_SQMI|AWATER_SQMI|INTPTLAT|INTPTLONG``. Every
  source row has these columns; they are None for a ZIP without a ZCTA.
- Census Gazetteer counties file (about 0.1 MB): the name, the state and the internal
  point of every county.
- BTS NTAD Time Zones (about 9 MB of GeoJSON, one polygon per standard-time zone).

Any other column is absent when its file does not list the ZIP. The Fields decide
the order in which they fall back from one source to the next.

A ZIP has one HUD record per county it spans (about 29% span more than one). The
main county is the one with the largest share of the ZIP's residential addresses,
then of all its addresses, then the lowest county code. ``hud_counties`` lists the
counties in that order, each with its code, its Gazetteer name and state, and the
four shares of HUD. HUD writes an incomplete code for a few ZIPs; such a record is
not a county and is left out.

A time zone needs a point. These columns hold a zone, each from a coarser point:

- ``zcta_zone``: the zone that contains the internal point of the ZCTA;
- ``county_zone``: the zone that contains the internal point of the main county;
- ``v2_county_zone``: the same for the county that 2.x names (``v2_county`` in
  ``v2_state``), for ZIPs that HUD does not list;
- ``hud_state_zone``, ``zbp_state_zone``, ``v2_state_zone``: the zone of that state,
  when the internal points of all its counties lie in one zone.

The ZCTA point, the county point and the county of a ZIP are in three files, and a
second crawler could not download one of them again (rule C8). This is why those
files and the time zones are one crawler.
"""

import csv
import io
import json
import math
import sqlite3
import zipfile

from ..zipcodes import normalize_zip
from ..core import Crawler, Download, field_names
from ..keys import HUD_TOKEN
from ..fields import (
    zipcode_type, major_city, state, county, county_fips, county_list, lat, lng, timezone, land_area_in_sqmi,
    water_area_in_sqmi,
)

HUD_URL = "https://www.huduser.gov/hudapi/public/usps?type=2&query=All"
HUD_FILENAME = "hud_zip_county_all.json"
COUNTIES_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
    "2025_Gazetteer/2025_Gaz_counties_national.zip"
)
COUNTIES_FILENAME = "2025_Gaz_counties_national.zip"
ZBP_URL = "https://www2.census.gov/programs-surveys/cbp/datasets/2023/zbp23totals.zip"
ZBP_FILENAME = "zbp23totals.zip"
V2_URL = "https://github.com/MacHu-GWU/uszipcode-project/releases/download/1.0.1.db/simple_db.sqlite"
V2_FILENAME = "v2_simple_db.sqlite"
ZCTA_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
    "2025_Gazetteer/2025_Gaz_zcta_national.zip"
)
ZCTA_FILENAME = "2025_Gaz_zcta_national.zip"
BTS_URL = ("https://services.arcgis.com/xOi1kZaI0eWDREZv/ArcGIS/rest/services/NTAD_Time_Zones/FeatureServer/0/"
           "query?where=1%3D1&outFields=zone,utc&outSR=4326&f=geojson")
BTS_FILENAME = "ntad_time_zones.geojson"

POINT_COLUMNS = ("INTPTLAT", "INTPTLONG")  # of both Gazetteer files
STATE_COLUMNS = ("hud_state", "zbp_state", "v2_state")
RATIOS = ("res_ratio", "bus_ratio", "oth_ratio", "tot_ratio")  # of a HUD record: the shares of the ZIP's addresses
BAND = 0.01  # degrees of latitude per bucket of zone edges


def _zip_text(path: str, encoding: str) -> str:
    with zipfile.ZipFile(path) as z:
        members = [n for n in z.namelist() if n.lower().endswith(".txt")]
        if len(members) != 1:
            raise ValueError("expected one .txt file in %s, found %s" % (path, members))
        return z.read(members[0]).decode(encoding)


def _gazetteer(path):
    """(header, rows) of a Gazetteer file (pipe- or tab-delimited, depending on the year), every cell stripped."""
    text = _zip_text(path, "utf-8")
    delimiter = "|" if "|" in text.split("\n", 1)[0] else "\t"
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    header = [h.strip() for h in next(reader)]
    return header, [dict(zip(header, [cell.strip() for cell in row])) for row in reader if row]


class TimeZones:
    """The BTS zone polygons, with their edges in bands of latitude so that a lookup reads few edges."""

    def __init__(self, features):
        self.zones = []
        for feature in features:
            geometry = feature["geometry"]
            parts = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
            edges, xs, ys = {}, [], []
            for ring in (ring for part in parts for ring in part):
                ring = [tuple(p[:2]) for p in ring]
                if ring[0] != ring[-1]:
                    ring.append(ring[0])
                xs += [p[0] for p in ring]
                ys += [p[1] for p in ring]
                for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
                    if y1 != y2:  # a horizontal edge never crosses a horizontal ray
                        for band in range(math.floor(min(y1, y2) / BAND), math.floor(max(y1, y2) / BAND) + 1):
                            edges.setdefault(band, []).append((x1, y1, x2, y2))
            self.zones.append((dict(feature["properties"]), (min(xs), min(ys), max(xs), max(ys)), edges))

    def find(self, x: float, y: float) -> dict:
        """The properties of the first zone that contains the point (even-odd rule), else {}."""
        band = math.floor(y / BAND)
        for properties, (x_min, y_min, x_max, y_max), edges in self.zones:
            if x_min <= x <= x_max and y_min <= y <= y_max:
                inside = False
                for x1, y1, x2, y2 in edges.get(band, ()):
                    if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                        inside = not inside
                if inside:
                    return properties
        return {}

    def zone_at(self, row) -> str:
        """The name of the zone at the internal point of a Gazetteer row, else None."""
        latitude, longitude = (row.get(c) for c in POINT_COLUMNS)
        return self.find(float(longitude), float(latitude)).get("zone") if latitude and longitude else None


def _main_county_first(record):
    return -float(record.get("res_ratio") or 0), -float(record.get("tot_ratio") or 0), str(record.get("geoid"))


def _county_list(records, counties):
    """The HUD records of one ZIP, in order, as JSON text; None if none of them has a 5-digit county code."""
    listed = []
    for record in records:
        code = str(record.get("geoid") or "")
        if len(code) == 5 and code.isdigit():
            county = counties.get(code, {})
            listed.append(dict({"county_fips": code, "county": county.get("NAME"), "state": county.get("USPS")},
                               **{name: record.get(name) for name in RATIOS}))
    return json.dumps(listed, separators=(",", ":"), ensure_ascii=False) if listed else None


def _read_hud(path, counties):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)["data"]
    by_zip = {}
    for rec in data["results"] if isinstance(data, dict) else data:  # one record per county of the ZIP
        by_zip.setdefault(rec.get("zip"), []).append(rec)
    for key, records in by_zip.items():
        records.sort(key=_main_county_first)
        city = next((r.get("city") for r in records if r.get("city")), None)
        state = next((r.get("state") for r in records if r.get("state")), None)
        fips = str(records[0].get("geoid") or "")
        yield key, {"hud_city": city, "hud_state": state, "hud_county_fips": fips,
                    "hud_county_name": counties.get(fips, {}).get("NAME"),
                    "hud_counties": _county_list(records, counties)}


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


def _read_zcta(rows):
    for row in rows:
        yield row.get("GEOID"), row


def _county_key(usps, name):
    return (usps or "").strip().upper(), (name or "").strip().casefold()


def _zones_of_places(counties, zones):
    """
    Three lookups of a zone: {county code: zone at its internal point}, the same by
    ``_county_key`` (state and county name), and {state: its zone}. A state has a zone
    when all its counties are in the same one; so has a name that two counties share.
    """
    by_code, by_name, by_state = {}, {}, {}
    for row in counties:
        zone = zones.zone_at(row)
        if zone:
            by_code[row.get("GEOID")] = zone
        by_name.setdefault(_county_key(row.get("USPS"), row.get("NAME")), set()).add(zone)
        by_state.setdefault(row.get("USPS"), set()).add(zone)

    def only(found):
        return {key: next(iter(zones_)) for key, zones_ in found.items() if len(zones_) == 1 and None not in zones_}
    return by_code, only(by_name), only(by_state)


def parse(files):
    _, counties = _gazetteer(files[COUNTIES_FILENAME])
    counties_by_code = {row.get("GEOID"): row for row in counties}
    zcta_header, zctas = _gazetteer(files[ZCTA_FILENAME])
    with open(files[BTS_FILENAME], encoding="utf-8") as fh:
        zones = TimeZones(json.load(fh)["features"])
    county_zones, named_county_zones, state_zones = _zones_of_places(counties, zones)

    rows = {}
    sources = (_read_hud(files[HUD_FILENAME], counties_by_code), _read_zbp(files[ZBP_FILENAME]),
               _read_v2(files[V2_FILENAME]), _read_zcta(zctas))
    for source in sources:
        for key, values in source:
            zipcode = normalize_zip(key)
            if zipcode:
                row = rows.setdefault(zipcode, dict.fromkeys(zcta_header))
                for name, value in values.items():
                    if value and not row.get(name):
                        row[name] = value
    for row in rows.values():
        found = {"zcta_zone": zones.zone_at(row), "county_zone": county_zones.get(row.get("hud_county_fips")),
                 "v2_county_zone": named_county_zones.get(_county_key(row.get("v2_state"), row.get("v2_county")))}
        found.update((name + "_zone", state_zones.get(row.get(name))) for name in STATE_COLUMNS)
        row.update((name, zone) for name, zone in found.items() if zone)
    return iter(rows.items())


CRAWLER = Crawler(
    name="zip-basics",
    fields=field_names(zipcode_type, major_city, state, county, county_fips, county_list, lat, lng, timezone,
                       land_area_in_sqmi, water_area_in_sqmi),
    downloads=(
        Download(HUD_FILENAME, HUD_URL, magic=b"{", secret=HUD_TOKEN),
        Download(COUNTIES_FILENAME, COUNTIES_URL, magic=b"PK\x03\x04"),
        Download(ZBP_FILENAME, ZBP_URL, magic=b"PK\x03\x04"),
        Download(V2_FILENAME, V2_URL, magic=b"SQLite format 3\x00"),
        Download(ZCTA_FILENAME, ZCTA_URL, magic=b"PK\x03\x04"),
        Download(BTS_FILENAME, BTS_URL, magic=b"{"),
    ),
    parse=parse,
    description=("HUD-USPS crosswalk, Census Gazetteer ZCTAs and counties, Census ZBP, uszipcode 2.x, BTS time zones "
                 "-> ZIP type, city, state, counties, internal point, area, time zone"),
)
