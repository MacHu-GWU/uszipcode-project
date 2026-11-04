# -*- coding: utf-8 -*-

"""
The real crawlers: their parsers on real sample rows, and the whole demo through a
FakeOpener (no network).
"""

import dataclasses
import json
import os
import zipfile

from data_pipeline.database import fetch
from data_pipeline.database.cli import main
from data_pipeline.database.core import Paths
from data_pipeline.database.crawl import check_rows
from data_pipeline.database.crawlers import CRAWLERS, census_dhc, census_gazetteer
from data_pipeline.database.fields import FIELDS

from fakes import FakeOpener

KEY = "SECRET-TEST-123"
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


def test_demo_database(tmp_path, monkeypatch, capsys):
    """The real registry and the repo mise.toml, with the sample files served by a FakeOpener."""
    with open(_gazetteer_zip(tmp_path), "rb") as fh:
        gazetteer = fh.read()
    opener = FakeOpener({census_gazetteer.URL: gazetteer, census_dhc.URL: json.dumps(DHC).encode()})
    monkeypatch.setattr(fetch, "urlopen", opener)
    monkeypatch.setenv("CENSUS_API_KEY", KEY)
    root = tmp_path / "repo"
    paths = dataclasses.replace(Paths.under(str(root)), mise_toml=Paths.default().mise_toml)

    assert main(["crawl", "--all"], FIELDS, CRAWLERS, paths=paths) == 0
    assert opener.urls == [census_gazetteer.URL, census_dhc.URL + "&key=" + KEY]
    assert main(["crawl", "--all"], FIELDS, CRAWLERS, paths=paths) == 0
    assert len(opener.calls) == 2  # cached: no new request
    assert main(["build"], FIELDS, CRAWLERS, paths=paths) == 0
    with open(os.path.join(paths.db_out_dir, "db_demo.csv"), "rb") as fh:
        assert fh.read() == (b"zipcode,lat,lng,land_area_in_sqmi,population,housing_units\n"
                             b"10001,40.750649,-73.997298,0.624,32612,18926\n"
                             b"20013,,,,,\n"
                             b"20037,38.892459,-77.053811,0.732,14945,9689\n")
    with open(os.path.join(paths.db_out_dir, "db_demo_coverage.json"), encoding="utf-8") as fh:
        coverage = json.load(fh)
    assert coverage["pks_without_any_value"] == ["20013"]
    assert {f: c["share"] for f, c in coverage["fields"].items()} == dict.fromkeys(
        ["lat", "lng", "land_area_in_sqmi", "population", "housing_units"], 0.6667)
    assert coverage["crawlers"]["census-dhc"]["rows_outside_pk_set"] == 1  # 00601

    out, err = capsys.readouterr()
    assert KEY not in out + err
    for folder, _, names in os.walk(str(root)):
        for n in names:
            with open(os.path.join(folder, n), "rb") as fh:
                assert KEY.encode() not in fh.read(), n
