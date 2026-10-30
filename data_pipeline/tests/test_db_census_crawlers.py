# -*- coding: utf-8 -*-

"""
The two real crawlers: their parsers on real sample rows, the whole demo through a
FakeOpener (no network), and a check that crawler modules never touch the network.
"""

import ast
import dataclasses
import json
import os
import zipfile

from data_pipeline.database import fetch
from data_pipeline.database.cli import main
from data_pipeline.database.core import Paths
from data_pipeline.database.crawlers import census_dhc, census_gazetteer

from fakes import FakeOpener

KEY = "SECRET-TEST-123"
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


def test_gazetteer_parse(tmp_path):
    rows = dict(census_gazetteer.parse({census_gazetteer.FILENAME: _gazetteer_zip(tmp_path)}))
    assert rows == {
        "00601": {"lat": 18.180555, "lng": -66.749961, "land_area_in_sqmi": 64.416},
        "10001": {"lat": 40.750649, "lng": -73.997298, "land_area_in_sqmi": 0.624},
        "20037": {"lat": 38.892459, "lng": -77.053811, "land_area_in_sqmi": 0.732},
    }


def test_dhc_parse(tmp_path):
    rows = list(census_dhc.parse({census_dhc.FILENAME: _dhc_json(tmp_path)}))
    assert rows == [("00601", {"population": 17242, "housing_units": 7605}),
                    ("10001", {"population": 32612, "housing_units": 18926}),
                    ("20037", {"population": 14945, "housing_units": 9689})]


def test_demo_database(tmp_path, monkeypatch, capsys):
    """The real registry and the repo mise.toml, with the sample files served by a FakeOpener."""
    with open(_gazetteer_zip(tmp_path), "rb") as fh:
        gazetteer = fh.read()
    opener = FakeOpener({census_gazetteer.URL: gazetteer, census_dhc.URL: json.dumps(DHC).encode()})
    monkeypatch.setattr(fetch, "urlopen", opener)
    monkeypatch.setenv("CENSUS_API_KEY", KEY)
    root = tmp_path / "repo"
    paths = dataclasses.replace(Paths.under(str(root)), mise_toml=Paths.default().mise_toml)

    assert main(["crawl", "--all"], paths=paths) == 0
    assert opener.urls == [census_gazetteer.URL, census_dhc.URL + "&key=" + KEY]
    assert main(["crawl", "--all"], paths=paths) == 0
    assert len(opener.calls) == 2  # cached: no new request
    assert main(["build"], paths=paths) == 0
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


def test_crawler_modules_never_touch_the_network():
    forbidden = {"urllib", "http", "socket", "ssl", "requests"}
    folder = os.path.dirname(census_dhc.__file__)
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".py"):
            continue
        with open(os.path.join(folder, name), encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                modules = [base] + ["%s.%s" % (base, a.name) for a in node.names]
            else:
                continue
            for m in modules:
                assert m.split(".")[0] not in forbidden, (name, m)
                assert m.split(".")[-1] != "fetch", (name, m)
