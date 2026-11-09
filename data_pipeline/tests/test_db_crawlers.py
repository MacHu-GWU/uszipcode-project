# -*- coding: utf-8 -*-

"""
The real crawlers: their parsers on real sample rows, and the whole demo through a
FakeOpener (no network).
"""

import csv
import dataclasses
import io
import json
import os
import sqlite3
import struct
import zipfile

import pytest

from data_pipeline.database import fetch
from data_pipeline.database.cli import main
from data_pipeline.database.core import Paths
from data_pipeline.database.crawl import check_rows
from data_pipeline.database.crawlers import (
    CRAWLERS, census_acs5, census_acs5_history, census_decennial, census_dhc, census_gazetteer, irs_soi, zip_basics,
    zcta_geometry,
)
from data_pipeline.database.fields import FIELDS
from data_pipeline.database.fields.history import HISTORY_FIELDS

from fakes import FakeOpener

KEY = "SECRET-TEST-123"
TOKEN = "SECRET-TOKEN-456"
CATALOG = {f.name: f for f in FIELDS}
# real rows of the 2025 Gazetteer ZCTA file; the padded last header name is how older vintages look
GAZETTEER = (
    "GEOID|GEOIDFQ|ALAND|AWATER|ALAND_SQMI|AWATER_SQMI|INTPTLAT|INTPTLONG    \n"
    "00601|860Z200US00601|166836450|798613|64.416|0.308|18.180555|-66.749961\n"
    "10001|860Z200US10001|1616221|0|0.624|0.|40.750649|-73.997298\n"
    "20037|860Z200US20037|1896195|597667|0.732|0.231|38.892459|-77.053811 \n"
)
# real DHC values for 20037 and 10001; every other variable is 1
DHC_VALUES = {
    "00601": {"P1_001N": "17242", "H1_001N": "7605"},
    "10001": {"P1_001N": "32612", "H1_001N": "18926"},
    "20037": {"P1_001N": "14945", "H1_001N": "9689", "H3_002N": "8178", "H3_003N": "1511", "P12_003N": "158"},
}
# the shapes of the real files: 42223 spans two counties, 00501 is not in HUD here, 09001 only in 2.x
HUD = {"data": {"year": "2026", "quarter": "2", "results": [
    {"zip": "10001", "geoid": "36061", "res_ratio": 1, "bus_ratio": 1, "oth_ratio": 1, "tot_ratio": 1, "city": "NEW YORK", "state": "NY"},
    {"zip": "20013", "geoid": "11001", "res_ratio": 1, "bus_ratio": 1, "oth_ratio": 1, "tot_ratio": 1, "city": "WASHINGTON", "state": "DC"},
    {"zip": "20037", "geoid": "11001", "res_ratio": 1, "bus_ratio": 1, "oth_ratio": 1, "tot_ratio": 1, "city": "WASHINGTON", "state": "DC"},
    {"zip": "42223", "geoid": "21047", "res_ratio": 0.089, "bus_ratio": 0.418, "oth_ratio": 0.306, "tot_ratio": 0.106,
     "city": "FORT CAMPBELL", "state": "KY"},
    {"zip": "42223", "geoid": "47125", "res_ratio": 0.911, "bus_ratio": 0.582, "oth_ratio": 0.694, "tot_ratio": 0.894,
     "city": "FORT CAMPBELL", "state": "KY"},
    {"zip": "77352", "geoid": "48", "res_ratio": 0, "bus_ratio": 0, "oth_ratio": 1, "tot_ratio": 1, "city": "HOUSTON", "state": "TX"},
]}}
COUNTIES = ("USPS|GEOID|ANSICODE|NAME|ALAND|AWATER|ALAND_SQMI|AWATER_SQMI|INTPTLAT|INTPTLONG\n"
            "DC|11001|01702382|District of Columbia|158316181|18709762|61.126|7.224|38.904|-77.016\n"
            "KY|21047|00516870|Christian County|1855209014|11396406|716.302|4.400|36.892|-87.490\n"
            "NY|36061|00974129|New York County|58690498|28541727|22.661|11.020|40.776|-73.970\n"
            "TN|47125|01648580|Montgomery County|1394406843|12813398|538.384|4.947|36.497|-87.383\n")
ZBP = 'zip,name,est,city,stabbr\n00501,"HOLTSVILLE, NY",3,HOLTSVILLE,NY\n99999,UNCLASSIFIED,10,,\n10001,"NEW YORK, NY",9,NEW YORK,NY\n'
V2 = [("09001", "MILITARY", "Apo", None, "AE"), ("10001", "STANDARD", "New York", "New York County", "NY"),
      ("20013", "PO BOX", "Washington", "District of Columbia", "DC"),
      ("20037", "STANDARD", "Washington", "District of Columbia", "DC"),
      ("00501", "UNIQUE", "Holtsville", "Suffolk County", "NY"), ("77352", "STANDARD", "Houston", "Montgomery County", "TX")]


def _zip_file(path, member, text, encoding="utf-8") -> str:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(member, text.encode(encoding))
    return path


def _dhc_responses() -> dict:
    """filename -> the JSON body the Census API returns for that request."""
    out = {}
    for filename, variables in census_dhc.REQUESTS:
        rows = [list(variables) + [census_dhc.KEY_COLUMN]]
        for zcta, values in DHC_VALUES.items():
            rows.append([values.get(v, "1") for v in variables] + [zcta])
        out[filename] = json.dumps(rows).encode()
    return out


# real ACS 2019-2023 values for 20037; 10001 has a "not available" median; every other variable is 1
ACS_VALUES = {
    "00601": {},
    "10001": {"B25077_001E": "-666666666", "B25077_001M": "-222222222"},
    "20037": {"B01002_001E": "31.3", "B25077_001E": "743700", "B19013_001E": "98917", "B25064_001E": "2420",
              "B17001_001E": "12357", "B17001_002E": "2215"},
}


# the shape of the IRS file: lower-case agi_stub, numbers with decimals, state totals (00000) and pooled ZIPs (99999);
# the 20037 row has the real tax year 2022 values
IRS_COLUMNS = ("N1", "N00200", "A00200", "N00900", "A00900", "N26270", "A26270", "N02300", "A02300", "N00300", "A00300",
               "N00600", "A00600", "N00650", "A00650", "N01000", "A01000", "N01400", "A01400", "N01700", "A01700",
               "N02500", "A02500")
IRS_20037 = ("5460", "4390", "539853", "870", "37601", "400", "79281", "70", "547", "2760", "14943", "2660", "52371",
             "2550", "39400", "2310", "73715", "730", "39781", "840", "52110", "750", "22101")


def _irs_csv() -> str:
    lines = ["STATEFIPS,STATE,ZIPCODE,agi_stub," + ",".join(IRS_COLUMNS)]
    for fips, state, zipcode, values in (("11", "DC", "00000", ["100"] * len(IRS_COLUMNS)),
                                         ("11", "DC", "20037", IRS_20037),
                                         ("36", "NY", "10001", ["10"] * len(IRS_COLUMNS)),
                                         ("36", "NY", "99999", ["10"] * len(IRS_COLUMNS))):
        lines.append("%s,%s,%s,0,%s" % (fips, state, zipcode, ",".join(v + ".0000" for v in values)))
    return "\n".join(lines) + "\n"


def _acs_responses(year=census_acs5.YEAR) -> dict:
    out = {}
    for part, variables in census_acs5.REQUESTS:
        rows = [list(variables) + [census_acs5.KEY_COLUMN]]
        for zcta, values in ACS_VALUES.items():
            rows.append([values.get(v, "1") for v in variables] + [zcta])
        out[census_acs5.filename(year, part)] = json.dumps(rows).encode()
    return out


def _dhc_files(folder) -> dict:
    files = {}
    for filename, body in _dhc_responses().items():
        files[filename] = os.path.join(str(folder), filename)
        with open(files[filename], "wb") as fh:
            fh.write(body)
    return files


def _zip_basics_files(folder) -> dict:
    hud = os.path.join(str(folder), zip_basics.HUD_FILENAME)
    with open(hud, "w", encoding="utf-8") as fh:
        json.dump(HUD, fh)
    v2 = os.path.join(str(folder), zip_basics.V2_FILENAME)
    con = sqlite3.connect(v2)
    con.execute("CREATE TABLE simple_zipcode (zipcode TEXT, zipcode_type TEXT, major_city TEXT, county TEXT, state TEXT)")
    con.executemany("INSERT INTO simple_zipcode VALUES (?, ?, ?, ?, ?)", V2)
    con.commit()
    con.close()
    return {
        zip_basics.HUD_FILENAME: hud,
        zip_basics.COUNTIES_FILENAME: _zip_file(os.path.join(str(folder), zip_basics.COUNTIES_FILENAME),
                                                "2025_Gaz_counties_national.txt", COUNTIES),
        zip_basics.ZBP_FILENAME: _zip_file(os.path.join(str(folder), zip_basics.ZBP_FILENAME),
                                           "zbp23totals.txt", ZBP, "latin-1"),
        zip_basics.V2_FILENAME: v2,
    }


def _read(path) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


# ---------------------------------------------------------------------------- shapefiles for zcta-geometry
def _dbf(columns, rows) -> bytes:
    """A dBase III file of text columns."""
    widths = [max([1] + [len(r[i]) for r in rows]) for i in range(len(columns))]
    out = bytearray(struct.pack("<4BIHH20x", 3, 126, 1, 1, len(rows), 33 + 32 * len(columns), 1 + sum(widths)))
    for name, width in zip(columns, widths):
        out += struct.pack("<11sc4xBB14x", name.encode(), b"C", width, 0)
    out += b"\r"
    for r in rows:
        out += b" " + b"".join(value.encode().ljust(width) for value, width in zip(r, widths))
    return bytes(out + b"\x1a")


def _shp(shapes) -> bytes:
    """A polygon shapefile; a shape is None (null shape) or a list of closed rings of (x, y)."""
    records = bytearray()
    for number, shape in enumerate(shapes, start=1):
        if shape is None:
            content = struct.pack("<i", 0)
        else:
            points = [p for ring in shape for p in ring]
            xs, ys = [p[0] for p in points], [p[1] for p in points]
            starts = [sum(len(r) for r in shape[:i]) for i in range(len(shape))]
            content = struct.pack("<i4d2i", 5, min(xs), min(ys), max(xs), max(ys), len(shape), len(points))
            content += struct.pack("<%di" % len(shape), *starts) + b"".join(struct.pack("<2d", *p) for p in points)
        records += struct.pack(">2i", number, len(content) // 2) + content
    header = struct.pack(">i20xi", 9994, (100 + len(records)) // 2) + struct.pack("<2i8d", 1000, 5, *[0.0] * 8)
    return header + bytes(records)


def _shapefile_zip(path, stem, columns, rows, shapes) -> str:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(stem + ".shp", _shp(shapes))
        z.writestr(stem + ".dbf", _dbf(columns, rows))
        z.writestr(stem + ".shp.iso.xml", "<metadata/>")
    return path


def _box(west, south, east, north):
    """A clockwise ring (an outer ring in a shapefile)."""
    return [(west, south), (west, north), (east, north), (east, south), (west, south)]


# the real boxes and internal points of 20037 and 10001; 99546 is a made-up shape across the 180th meridian
BOX_20037, BOX_10001 = (-77.064696, 38.87131, -77.04624, 38.910414), (-74.010148, 40.743451, -73.984076, 40.759686)
TIGER_ROWS = [("20037", "+38.8924590", "-077.0538110"), ("10001", "+40.7506490", "-073.9972980"),
              ("99546", "+51.8800000", "+179.8000000"), ("00000", "", "")]
TIGER_SHAPES = [[_box(*BOX_20037)], [_box(*BOX_10001)],
                [_box(179.5, 51.8, 180.0, 51.9), _box(-180.0, 51.8, -179.5, 51.9)], None]
HOLE = [(-77.06, 38.89), (-77.05, 38.89), (-77.05, 38.90), (-77.06, 38.90), (-77.06, 38.89)]  # counter-clockwise
CB_ROWS = [("10001",), ("20037",), ("00601",)]
CB_SHAPES = [[_box(-74.01, 40.74, -74.0, 40.75), _box(-73.99, 40.75, -73.98, 40.76)],
             [_box(*BOX_20037), HOLE],
             [_box(-66.8366661, 18.11, -66.66, 18.25)]]
TIME_ZONES = {"type": "FeatureCollection", "features": [
    {"type": "Feature", "properties": {"zone": "Central", "utc": "-06:00"},
     "geometry": {"type": "Polygon", "coordinates": [[[-90, 30], [-80, 30], [-80, 45], [-90, 45], [-90, 30]]]}},
    {"type": "Feature", "properties": {"zone": "Eastern", "utc": "-05:00"},
     "geometry": {"type": "MultiPolygon", "coordinates": [
         [[[-80, 30], [-70, 30], [-70, 45], [-80, 45], [-80, 30]],
          [[-77.06, 38.85], [-77.0, 38.85], [-77.0, 38.88], [-77.06, 38.88], [-77.06, 38.85]]],  # a hole
         [[[-67, 17], [-65, 17], [-65, 19], [-67, 19]]]]}},  # an open ring: closed when read
]}


def _geometry_files(folder) -> dict:
    folder = str(folder)
    bts = os.path.join(folder, zcta_geometry.BTS_FILENAME)
    with open(bts, "w", encoding="utf-8") as fh:
        json.dump(TIME_ZONES, fh)
    return {
        zcta_geometry.TIGER_FILENAME: _shapefile_zip(os.path.join(folder, zcta_geometry.TIGER_FILENAME),
                                                     "tl_2025_us_zcta520", ("ZCTA5CE20", "INTPTLAT20", "INTPTLON20"),
                                                     TIGER_ROWS, TIGER_SHAPES),
        zcta_geometry.CB_FILENAME: _shapefile_zip(os.path.join(folder, zcta_geometry.CB_FILENAME),
                                                  "cb_2020_us_zcta520_500k", ("ZCTA5CE20",), CB_ROWS, CB_SHAPES),
        zcta_geometry.BTS_FILENAME: bts,
    }


def test_gazetteer(tmp_path):
    files = {census_gazetteer.FILENAME: _zip_file(str(tmp_path / census_gazetteer.FILENAME),
                                                  "2025_Gaz_zcta_national.txt", GAZETTEER)}
    rows = dict(census_gazetteer.parse(files))
    assert rows["10001"]["INTPTLAT"] == "40.750649" and rows["20037"]["INTPTLONG"] == "-77.053811"
    records, _ = check_rows(census_gazetteer.CRAWLER, CATALOG, census_gazetteer.parse(files))
    assert records == [("00601", [18.180555, -66.749961, 64.416, 0.308]),
                       ("10001", [40.750649, -73.997298, 0.624, 0.0]),
                       ("20037", [38.892459, -77.053811, 0.732, 0.231])]


@pytest.mark.parametrize("module", [census_dhc, census_acs5], ids=["census-dhc", "census-acs5"])
def test_census_requests_fit_the_api(module):
    for name, variables in module.REQUESTS:
        assert len(variables) <= 50 and len(set(variables)) == len(variables), name
    assert len(set(module.VARIABLES)) == len(module.VARIABLES)


@pytest.mark.parametrize("module", [census_dhc, census_acs5], ids=["census-dhc", "census-acs5"])
def test_census_requests_have_every_variable_their_fields_read(module):
    row = dict.fromkeys(module.VARIABLES, "1")
    for name in module.CRAWLER.fields:
        assert CATALOG[name].extract(row) is not None, name  # a KeyError means a variable is not requested


def test_acs(tmp_path):
    files = {}
    for filename, body in _acs_responses().items():
        files[filename] = str(tmp_path / filename)
        with open(files[filename], "wb") as fh:
            fh.write(body)
    records, _ = check_rows(census_acs5.CRAWLER, CATALOG, census_acs5.CRAWLER.parse(files))
    values = {z: dict(zip(census_acs5.CRAWLER.fields, v)) for z, v in records}
    assert [values["20037"][k] for k in ("median_age", "median_home_value", "median_household_income", "median_rent")] \
        == [31.3, 743700, 98917, 2420]
    assert values["20037"]["poverty_rate"] == 2215 / 12357
    assert values["10001"]["median_home_value"] is None and values["10001"]["median_home_value_moe"] is None
    assert values["20037"]["owner_occupied_home_values_lt100k"] == 13  # B25075_002E ... B25075_014E
    assert values["20037"]["educational_attainment_less_than_high_school"] == 15


def test_irs(tmp_path):
    path = tmp_path / irs_soi.filename(irs_soi.YEAR)
    path.write_text(_irs_csv(), encoding="utf-8")
    files = {irs_soi.filename(irs_soi.YEAR): str(path)}
    records, stats = check_rows(irs_soi.CRAWLER, CATALOG, irs_soi.CRAWLER.parse(files))
    assert [z for z, _ in records] == ["10001", "20037"] and stats["skipped_keys"] == 2  # 00000 and 99999
    values = dict(zip(irs_soi.CRAWLER.fields, dict(records)["20037"]))
    # the research checked these shares of 20037 against the reference values (rounded to whole percent)
    assert round(100 * values["sources_of_household_income_wages_share"], 1) == 80.4
    assert round(100 * values["household_investment_income_capital_gains_share"], 1) == 42.3
    assert round(100 * values["household_retirement_income_social_security_share"], 1) == 13.7
    assert values["sources_of_household_income_wages_average"] == 122973  # 539,853 thousand / 4,390 returns
    assert values["household_retirement_income_pensions_annuities_average"] == 62036


def test_irs_tax_year_is_in_the_url_and_file_name():
    old = irs_soi.crawler_for(2022)
    assert old.downloads[0].url == "https://www.irs.gov/pub/irs-soi/22zpallnoagi.csv"
    assert old.downloads[0].filename == "22zpallnoagi.csv" and old.fields == irs_soi.CRAWLER.fields


def _census_json(header_variables, values_by_zcta, key_column="zip code tabulation area") -> bytes:
    rows = [list(header_variables) + [key_column]]
    rows += [[values.get(v, "1") for v in header_variables] + [zcta] for zcta, values in values_by_zcta.items()]
    return json.dumps(rows).encode()


# real 20037 values of the research: ACS 2011 vintage and the three censuses
ACS_HISTORY_20037 = {2011: {"B01003_001E": "13642", "B19013_001E": "78081", "B25077_001E": "546500", "B25064_001E": "1659"}}
CENSUS_20037 = {2000: "12642", 2010: "14642", 2020: "14945"}


def _history_responses() -> dict:
    """url -> body for every download of the two history crawlers."""
    out = {}
    for year, d in zip(census_acs5_history.YEARS, census_acs5_history.CRAWLER.downloads):
        out[d.url] = _census_json(census_acs5_history.VARIABLES,
                                  {"10001": {}, "20037": ACS_HISTORY_20037.get(year, {})})
    for (year, (_, variable)), d in zip(census_decennial.CENSUSES.items(), census_decennial.CRAWLER.downloads):
        out[d.url] = _census_json([variable], {"10001": {}, "20037": {variable: CENSUS_20037[year]}})
    return out


def test_history_crawlers(tmp_path):
    served = _history_responses()
    for crawler in (census_acs5_history.CRAWLER, census_decennial.CRAWLER):
        files = {}
        for d in crawler.downloads:
            files[d.filename] = str(tmp_path / d.filename)
            with open(files[d.filename], "wb") as fh:
                fh.write(served[d.url])
        records, _ = check_rows(crawler, {f.name: f for f in HISTORY_FIELDS}, crawler.parse(files))
        values = {key: dict(zip(crawler.fields, v)) for key, v in records}
        if crawler is census_decennial.CRAWLER:
            assert [values[("20037", y)]["census_population"] for y in (2000, 2010, 2020)] == [12642, 14642, 14945]
            assert len(records) == 6
        else:
            assert values[("20037", 2011)]["acs_population"] == 13642 and values[("20037", 2011)]["median_rent"] == 1659
            assert sorted({y for _, y in values}) == list(range(2011, 2025)) and len(records) == 2 * 14


def test_acs_vintage_is_in_the_urls_and_file_names():
    old = census_acs5.crawler_for(2023)
    assert all("/data/2023/acs/acs5?" in d.url and d.filename.startswith("acs5_2023_") for d in old.downloads)
    assert old.fields == census_acs5.CRAWLER.fields and old.name == census_acs5.CRAWLER.name


def test_dhc(tmp_path):
    files = _dhc_files(tmp_path)
    rows = dict(census_dhc.parse(files))
    assert rows["10001"]["P1_001N"] == "32612" and rows["20037"]["PCT19_189N"] == "1"
    records, _ = check_rows(census_dhc.CRAWLER, CATALOG, census_dhc.parse(files))
    values = {z: dict(zip(census_dhc.CRAWLER.fields, v)) for z, v in records}
    assert (values["20037"]["population"], values["20037"]["housing_units"], values["20037"]["occupied_housing_units"]) \
        == (14945, 9689, 8178)
    assert values["20037"]["housing_occupancy_vacant"] == 1511
    assert values["20037"]["population_by_age_male_0_4"] == 158
    assert values["20037"]["population_by_age_male_20_24"] == 3  # P12_008N + P12_009N + P12_010N
    assert values["20037"]["housing_type_nursing"] == 6  # six sex and age groups


def test_zip_basics_merges_the_sources(tmp_path):
    files = _zip_basics_files(tmp_path)
    rows = dict(zip_basics.parse(files))
    assert rows["10001"] == {"hud_city": "NEW YORK", "hud_state": "NY", "hud_county_fips": "36061",
                             "hud_county_name": "New York County", "zbp_city": "NEW YORK", "zbp_state": "NY",
                             "v2_zipcode_type": "STANDARD", "v2_city": "New York", "v2_county": "New York County",
                             "v2_state": "NY"}
    assert "99999" not in rows
    records, stats = check_rows(zip_basics.CRAWLER, CATALOG, zip_basics.parse(files))
    assert dict(records) == {
        "00501": ["UNIQUE", "HOLTSVILLE", "NY", "Suffolk County", None],  # not in HUD: ZBP, then 2.x
        "09001": ["MILITARY", "APO", "AE", None, None],  # only in 2.x
        "10001": ["STANDARD", "NEW YORK", "NY", "New York County", "36061"],
        "20013": ["PO BOX", "WASHINGTON", "DC", "District of Columbia", "11001"],
        "20037": ["STANDARD", "WASHINGTON", "DC", "District of Columbia", "11001"],
        "42223": [None, "FORT CAMPBELL", "KY", "Montgomery County", "47125"],  # two counties: most residents in 47125
        "77352": ["STANDARD", "HOUSTON", "TX", "Montgomery County", None],  # HUD code "48" is incomplete
    }
    assert stats["non_null"]["county_fips"] == 4


def test_zcta_geometry(tmp_path):
    files = _geometry_files(tmp_path)
    rows = dict(zcta_geometry.parse(files))
    assert sorted(rows) == ["00000", "00601", "10001", "20037", "99546"]
    assert {k: rows["20037"][k] for k in ("INTPTLAT20", "INTPTLON20", "zone", "utc")} \
        == {"INTPTLAT20": "+38.8924590", "INTPTLON20": "-077.0538110", "zone": "Eastern", "utc": "-05:00"}
    assert rows["00601"]["Xmin"] is None and rows["00601"]["zone"] is None  # only in the cartographic file
    records, stats = check_rows(zcta_geometry.CRAWLER, CATALOG, zcta_geometry.parse(files))
    records = dict(records)
    assert records["20037"][:5] == [-77.064696, -77.04624, 38.910414, 38.87131, "Eastern"]
    assert json.loads(records["20037"][5]) == {"type": "Polygon", "coordinates": [  # reversed: RFC 7946 orientation
        [[-77.064696, 38.87131], [-77.04624, 38.87131], [-77.04624, 38.910414], [-77.064696, 38.910414],
         [-77.064696, 38.87131]],
        [[-77.06, 38.89], [-77.06, 38.9], [-77.05, 38.9], [-77.05, 38.89], [-77.06, 38.89]]]}
    assert json.loads(records["10001"][5])["type"] == "MultiPolygon" and records["10001"][4] == "Eastern"
    assert records["99546"][:5] == [179.5, -179.5, 51.9, 51.8, None]  # across the 180th meridian; no zone
    assert json.loads(records["00601"][5])["coordinates"][0][0] == [-66.836666, 18.11]  # 6 decimals
    assert stats["skipped_keys"] == 1  # 00000


def test_time_zone_lookup():
    zones = zcta_geometry.TimeZones(TIME_ZONES["features"])
    assert zones.find(-77.053811, 38.892459)["zone"] == "Eastern"
    assert zones.find(-87.6, 41.9)["zone"] == "Central"
    assert zones.find(-77.03, 38.86) == {}  # in the hole of Eastern
    assert zones.find(-66.0, 18.0)["zone"] == "Eastern"  # in the open ring, closed when read
    assert zones.find(-100.0, 40.0) == {}


def test_a_hole_goes_to_the_outer_ring_around_it():
    small, big = _box(-1, -1, 1, 1), _box(-10, -10, 10, 10)
    hole = [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5), (-0.5, -0.5)]
    content = _shp([[big, small, hole]])[108:]  # the first record, after the file and record headers
    geometry = json.loads(zcta_geometry.to_geojson(content))
    assert geometry["type"] == "MultiPolygon"
    assert [len(p) for p in geometry["coordinates"]] == [1, 2]  # the hole is in the small ring, not the big one


def test_demo_database(tmp_path, monkeypatch, capsys):
    """The real registry and the repo mise.toml, with the sample files served by a FakeOpener."""
    files = _zip_basics_files(tmp_path)
    dhc = _dhc_responses()
    served = {census_gazetteer.URL: _read(_zip_file(str(tmp_path / "gaz.zip"), "gaz.txt", GAZETTEER))}
    served.update({d.url: dhc[d.filename] for d in census_dhc.CRAWLER.downloads})
    acs = _acs_responses()
    served.update({d.url: acs[d.filename] for d in census_acs5.CRAWLER.downloads})
    served[irs_soi.CRAWLER.downloads[0].url] = _irs_csv().encode()
    served.update(_history_responses())
    served.update({d.url: _read(files[d.filename]) for d in zip_basics.CRAWLER.downloads})
    geometry = _geometry_files(tmp_path)
    served.update({d.url: _read(geometry[d.filename]) for d in zcta_geometry.CRAWLER.downloads})
    opener = FakeOpener(served)
    monkeypatch.setattr(fetch, "urlopen", opener)
    monkeypatch.setenv("CENSUS_API_KEY", KEY)
    monkeypatch.setenv("HUD_API_TOKEN", TOKEN)
    root = tmp_path / "repo"
    paths = dataclasses.replace(Paths.under(str(root)), mise_toml=Paths.default().mise_toml)

    kw = dict(paths=paths, history_fields=HISTORY_FIELDS)
    assert main(["crawl", "--all"], FIELDS, CRAWLERS, **kw) == 0
    downloads = [d for c in CRAWLERS for d in c.downloads]
    assert opener.urls == [d.url + ("&key=" + KEY if d.secret and d.secret.query_param else "") for d in downloads]
    assert opener.calls[downloads.index(zip_basics.CRAWLER.downloads[0])][1]["Authorization"] == "Bearer " + TOKEN
    assert main(["crawl", "--all"], FIELDS, CRAWLERS, **kw) == 0
    assert len(opener.calls) == len(downloads)  # cached: no new request
    assert main(["build"], FIELDS, CRAWLERS, **kw) == 0

    with open(os.path.join(paths.db_out_dir, "db_demo_history.csv"), encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == ["zipcode", "year"] + [f.name for f in HISTORY_FIELDS]
        history = {(r["zipcode"], int(r["year"])): r for r in reader}
    years = [2000, 2010] + list(range(2011, 2025))
    assert sorted(history) == [(z, y) for z in ("10001", "20037") for y in years]  # 20013 has no ZCTA: no history
    assert [history[("20037", y)]["census_population"] for y in (2000, 2010, 2020)] == ["12642", "14642", "14945"]
    assert history[("20037", 2011)]["median_home_value"] == "546500" and history[("20037", 2000)]["acs_population"] == ""

    with open(os.path.join(paths.db_out_dir, "db_demo.csv"), encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == ["zipcode"] + [f.name for f in FIELDS]
        rows = {r["zipcode"]: r for r in reader}
    assert sorted(rows) == ["10001", "20013", "20037"]
    assert [rows["20037"][k] for k in ("zipcode_type", "major_city", "state", "county", "county_fips", "lat",
                                       "water_area_in_sqmi", "population", "occupied_housing_units")] \
        == ["STANDARD", "WASHINGTON", "DC", "District of Columbia", "11001", "38.892459", "0.231", "14945", "8178"]
    assert [rows["20013"][k] for k in ("zipcode_type", "major_city", "state", "county")] \
        == ["PO BOX", "WASHINGTON", "DC", "District of Columbia"]
    census = [f.name for f in FIELDS if f.name not in zip_basics.CRAWLER.fields]
    assert all(rows["20013"][name] == "" for name in census)  # a PO box: no ZCTA, so no Census values
    with open(os.path.join(paths.db_out_dir, "db_demo_coverage.json"), encoding="utf-8") as fh:
        coverage = json.load(fh)
    assert rows["20037"]["median_home_value"] == "743700" and rows["10001"]["median_home_value"] == ""
    assert coverage["pks_by_non_null_fields"] == {"5": 1, str(len(FIELDS) - 2): 1, str(len(FIELDS)): 1}
    assert coverage["crawlers"]["census-dhc"]["rows_outside_pk_set"] == 1  # 00601

    out, err = capsys.readouterr()
    assert KEY not in out + err and TOKEN not in out + err
    for folder, _, names in os.walk(str(root)):
        for n in names:
            content = _read(os.path.join(folder, n))
            assert KEY.encode() not in content and TOKEN.encode() not in content, n
