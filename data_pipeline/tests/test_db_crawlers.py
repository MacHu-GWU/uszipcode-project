# -*- coding: utf-8 -*-

"""
The real crawlers: their parsers on real sample rows, and the whole demo through a
FakeOpener (no network).
"""

import dataclasses
import json
import os
import sqlite3
import zipfile

from data_pipeline.database import fetch
from data_pipeline.database.cli import main
from data_pipeline.database.core import Paths
from data_pipeline.database.crawl import check_rows
from data_pipeline.database.crawlers import CRAWLERS, census_dhc, census_gazetteer, zip_basics
from data_pipeline.database.fields import FIELDS

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
DHC = [["P1_001N", "H1_001N", "zip code tabulation area"],
       ["17242", "7605", "00601"], ["32612", "18926", "10001"], ["14945", "9689", "20037"]]
# the shapes of the real files: 42223 spans two counties, 00501 is not in HUD here, 09001 only in 2.x
HUD = {"data": {"year": "2026", "quarter": "2", "results": [
    {"zip": "10001", "geoid": "36061", "res_ratio": 1, "bus_ratio": 1, "oth_ratio": 1, "city": "NEW YORK", "state": "NY"},
    {"zip": "20013", "geoid": "11001", "res_ratio": 1, "bus_ratio": 1, "oth_ratio": 1, "city": "WASHINGTON", "state": "DC"},
    {"zip": "20037", "geoid": "11001", "res_ratio": 1, "bus_ratio": 1, "oth_ratio": 1, "city": "WASHINGTON", "state": "DC"},
    {"zip": "42223", "geoid": "21047", "res_ratio": 0.9, "bus_ratio": 0, "oth_ratio": 0, "city": "FORT CAMPBELL", "state": "KY"},
    {"zip": "42223", "geoid": "47125", "res_ratio": 0.1, "bus_ratio": 0, "oth_ratio": 0, "city": "FORT CAMPBELL", "state": "KY"},
]}}
ZBP = 'zip,name,est,city,stabbr\n00501,"HOLTSVILLE, NY",3,HOLTSVILLE,NY\n99999,UNCLASSIFIED,10,,\n10001,"NEW YORK, NY",9,NEW YORK,NY\n'
V2 = [("09001", "MILITARY", "Apo", "AE"), ("10001", "STANDARD", "New York", "NY"), ("20013", "PO BOX", "Washington", "DC"),
      ("20037", "STANDARD", "Washington", "DC"), ("00501", "UNIQUE", "Holtsville", "NY")]


def _gazetteer_zip(folder) -> str:
    path = os.path.join(str(folder), census_gazetteer.FILENAME)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("2025_Gaz_zcta_national.txt", GAZETTEER)
    return path


def _dhc_json(folder) -> str:
    path = os.path.join(str(folder), census_dhc.FILENAME)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(DHC, fh)
    return path


def _zip_basics_files(folder) -> dict:
    hud = os.path.join(str(folder), zip_basics.HUD_FILENAME)
    with open(hud, "w", encoding="utf-8") as fh:
        json.dump(HUD, fh)
    zbp = os.path.join(str(folder), zip_basics.ZBP_FILENAME)
    with zipfile.ZipFile(zbp, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("zbp23totals.txt", ZBP.encode("latin-1"))
    v2 = os.path.join(str(folder), zip_basics.V2_FILENAME)
    con = sqlite3.connect(v2)
    con.execute("CREATE TABLE simple_zipcode (zipcode TEXT, zipcode_type TEXT, major_city TEXT, state TEXT)")
    con.executemany("INSERT INTO simple_zipcode VALUES (?, ?, ?, ?)", V2)
    con.commit()
    con.close()
    return {zip_basics.HUD_FILENAME: hud, zip_basics.ZBP_FILENAME: zbp, zip_basics.V2_FILENAME: v2}


def _read(path) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def test_gazetteer(tmp_path):
    files = {census_gazetteer.FILENAME: _gazetteer_zip(tmp_path)}
    rows = dict(census_gazetteer.parse(files))
    assert rows["10001"]["INTPTLAT"] == "40.750649" and rows["20037"]["INTPTLONG"] == "-77.053811"
    records, _ = check_rows(census_gazetteer.CRAWLER, CATALOG, census_gazetteer.parse(files))
    assert records == [("00601", [18.180555, -66.749961, 64.416]),
                       ("10001", [40.750649, -73.997298, 0.624]),
                       ("20037", [38.892459, -77.053811, 0.732])]


def test_dhc(tmp_path):
    files = {census_dhc.FILENAME: _dhc_json(tmp_path)}
    assert dict(census_dhc.parse(files))["10001"]["P1_001N"] == "32612"
    records, _ = check_rows(census_dhc.CRAWLER, CATALOG, census_dhc.parse(files))
    assert records == [("00601", [17242, 7605]), ("10001", [32612, 18926]), ("20037", [14945, 9689])]


def test_zip_basics_merges_the_sources(tmp_path):
    files = _zip_basics_files(tmp_path)
    rows = dict(zip_basics.parse(files))
    assert rows["10001"] == {"hud_city": "NEW YORK", "hud_state": "NY", "zbp_city": "NEW YORK", "zbp_state": "NY",
                             "v2_zipcode_type": "STANDARD", "v2_city": "New York", "v2_state": "NY"}
    assert rows["00501"] == {"zbp_city": "HOLTSVILLE", "zbp_state": "NY", "v2_zipcode_type": "UNIQUE",
                             "v2_city": "Holtsville", "v2_state": "NY"}
    assert "99999" not in rows
    records, stats = check_rows(zip_basics.CRAWLER, CATALOG, zip_basics.parse(files))
    assert dict(records) == {
        "00501": ["UNIQUE", "HOLTSVILLE", "NY"],  # not in HUD: ZBP
        "09001": ["MILITARY", "APO", "AE"],  # only in 2.x
        "10001": ["STANDARD", "NEW YORK", "NY"],
        "20013": ["PO BOX", "WASHINGTON", "DC"],
        "20037": ["STANDARD", "WASHINGTON", "DC"],
        "42223": [None, "FORT CAMPBELL", "KY"],  # two HUD records, one row; no ZIP type
    }
    assert stats["non_null"] == {"zipcode_type": 5, "major_city": 6, "state": 6}


def test_demo_database(tmp_path, monkeypatch, capsys):
    """The real registry and the repo mise.toml, with the sample files served by a FakeOpener."""
    files = _zip_basics_files(tmp_path)
    opener = FakeOpener({
        census_gazetteer.URL: _read(_gazetteer_zip(tmp_path)),
        census_dhc.URL: json.dumps(DHC).encode(),
        zip_basics.HUD_URL: _read(files[zip_basics.HUD_FILENAME]),
        zip_basics.ZBP_URL: _read(files[zip_basics.ZBP_FILENAME]),
        zip_basics.V2_URL: _read(files[zip_basics.V2_FILENAME]),
    })
    monkeypatch.setattr(fetch, "urlopen", opener)
    monkeypatch.setenv("CENSUS_API_KEY", KEY)
    monkeypatch.setenv("HUD_API_TOKEN", TOKEN)
    root = tmp_path / "repo"
    paths = dataclasses.replace(Paths.under(str(root)), mise_toml=Paths.default().mise_toml)

    assert main(["crawl", "--all"], FIELDS, CRAWLERS, paths=paths) == 0
    assert opener.urls == [census_gazetteer.URL, census_dhc.URL + "&key=" + KEY,
                           zip_basics.HUD_URL, zip_basics.ZBP_URL, zip_basics.V2_URL]
    assert opener.calls[2][1]["Authorization"] == "Bearer " + TOKEN
    assert main(["crawl", "--all"], FIELDS, CRAWLERS, paths=paths) == 0
    assert len(opener.calls) == 5  # cached: no new request
    assert main(["build"], FIELDS, CRAWLERS, paths=paths) == 0
    assert _read(os.path.join(paths.db_out_dir, "db_demo.csv")) == (
        b"zipcode,zipcode_type,major_city,state,lat,lng,land_area_in_sqmi,population,housing_units\n"
        b"10001,STANDARD,NEW YORK,NY,40.750649,-73.997298,0.624,32612,18926\n"
        b"20013,PO BOX,WASHINGTON,DC,,,,,\n"
        b"20037,STANDARD,WASHINGTON,DC,38.892459,-77.053811,0.732,14945,9689\n")
    with open(os.path.join(paths.db_out_dir, "db_demo_coverage.json"), encoding="utf-8") as fh:
        coverage = json.load(fh)
    assert coverage["pks_without_any_value"] == []
    assert coverage["pks_by_non_null_fields"] == {"3": 1, "8": 2}
    assert {f: c["share"] for f, c in coverage["fields"].items()} == {
        "zipcode_type": 1.0, "major_city": 1.0, "state": 1.0, "lat": 0.6667, "lng": 0.6667,
        "land_area_in_sqmi": 0.6667, "population": 0.6667, "housing_units": 0.6667}
    assert coverage["crawlers"]["census-dhc"]["rows_outside_pk_set"] == 1  # 00601

    out, err = capsys.readouterr()
    assert KEY not in out + err and TOKEN not in out + err
    for folder, _, names in os.walk(str(root)):
        for n in names:
            content = _read(os.path.join(folder, n))
            assert KEY.encode() not in content and TOKEN.encode() not in content, n
