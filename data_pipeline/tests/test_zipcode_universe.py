# -*- coding: utf-8 -*-

"""
Offline tests for data_pipeline.zipcode_universe (no network).

Run from the repository root::

    python -m pytest data_pipeline/tests -q
"""

import csv
import os
import sqlite3
import tempfile

from data_pipeline.zipcode_universe.sources import (
    normalize_zip, is_military_zip, parse_gazetteer, parse_hud, parse_zbp, parse_irs, parse_v2,
)
from data_pipeline.zipcode_universe.build import merge, write_csv, summarize, COLUMNS, _parse_years


def test_normalize_zip():
    assert normalize_zip("501") == "00501"
    assert normalize_zip(" 20037 ") == "20037"
    assert normalize_zip("20037.0") == "20037"
    assert normalize_zip(601) == "00601"
    for bad in (None, "", "ABCDE", "123456", "00000", "99999", "2003-7"):
        assert normalize_zip(bad) is None


def test_is_military_zip():
    for z in ("09001", "09999", "34001", "96201", "96699"):
        assert is_military_zip(z)
    for z in ("08999", "10001", "33999", "34101", "96199", "96701"):
        assert not is_military_zip(z)


def test_parse_gazetteer():
    text = "GEOID|GEOIDFQ|ALAND\n00601|860Z200US00601|1\n20037|860Z200US20037|2\n"
    assert parse_gazetteer(text) == {"00601": {}, "20037": {}}


def test_parse_hud_combines_counties():
    payload = {"data": {"year": "2026", "quarter": "2", "results": [
        {"zip": "42223", "geoid": "21047", "res_ratio": 0.9, "bus_ratio": 0.2, "oth_ratio": 0, "city": "FORT CAMPBELL", "state": "KY"},
        {"zip": "42223", "geoid": "47125", "res_ratio": 0.1, "bus_ratio": 0.8, "oth_ratio": 0, "city": "FORT CAMPBELL", "state": "KY"},
        {"zip": "00501", "geoid": "36103", "res_ratio": 0, "bus_ratio": 1.0, "oth_ratio": 0, "city": "HOLTSVILLE", "state": "NY"},
    ]}}
    out = parse_hud(payload)
    assert out["42223"]["hud_county_count"] == 2
    assert out["42223"]["hud_has_residential"] and out["42223"]["hud_has_business"] and not out["42223"]["hud_has_other"]
    assert out["00501"] == {"city": "HOLTSVILLE", "state": "NY", "hud_has_residential": False,
                            "hud_has_business": True, "hud_has_other": False, "hud_county_count": 1}


def test_parse_zbp_skips_unclassified():
    text = "zip,name,est,city,stabbr\n00501,\"HOLTSVILLE, NY\",3,HOLTSVILLE,NY\n99999,UNCLASSIFIED,10,,\n"
    assert parse_zbp(text) == {"00501": {"city": "HOLTSVILLE", "state": "NY"}}


def test_parse_irs_header_case_and_totals():
    upper = "STATEFIPS,STATE,ZIPCODE,agi_stub,N1\n01,AL,00000,0,1\n01,AL,35004,0,5410\n01,AL,99999,0,7\n"
    lower = "STATEFIPS,STATE,zipcode,agi_stub,N1\n11,DC,20037,0,5460\n"
    assert parse_irs(upper) == {"35004": {"state": "AL"}}
    assert parse_irs(lower) == {"20037": {"state": "DC"}}


def test_parse_v2():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "v2.sqlite")
        con = sqlite3.connect(path)
        con.execute("CREATE TABLE simple_zipcode (zipcode TEXT, zipcode_type TEXT, major_city TEXT, state TEXT)")
        con.execute("INSERT INTO simple_zipcode VALUES ('09001', 'MILITARY', 'Apo', 'AE')")
        con.commit()
        con.close()
        assert parse_v2(path) == {"09001": {"v2_zipcode_type": "MILITARY", "city": "Apo", "state": "AE"}}


def _records():
    return {
        "census_zcta": {"20037": {}},
        "hud": {"20037": {"city": "WASHINGTON", "state": "DC", "hud_has_residential": True,
                          "hud_has_business": True, "hud_has_other": False, "hud_county_count": 1}},
        "zbp": {"20037": {"city": "WASHINGTON", "state": "DC"}, "00501": {"city": "HOLTSVILLE", "state": "NY"}},
        "irs": {"20037": {"state": "DC", "irs_years": [2021, 2022]}},
        "v2": {"20037": {"v2_zipcode_type": "STANDARD", "city": "Washington", "state": "DC"},
               "09001": {"v2_zipcode_type": "MILITARY", "city": "Apo", "state": "AE"}},
    }


def test_merge_flags_and_priorities():
    rows = {r["zipcode"]: r for r in merge(_records())}
    assert sorted(rows) == ["00501", "09001", "20037"]
    r = rows["20037"]
    assert (r["in_census_zcta"], r["in_hud"], r["in_zbp"], r["in_irs"], r["in_v2"]) == (1, 1, 1, 1, 1)
    assert r["n_gov_sources"] == 4 and r["city"] == "WASHINGTON" and r["city_source"] == "hud"
    assert r["irs_years"] == "2021;2022" and r["v2_zipcode_type"] == "STANDARD" and r["is_military_prefix"] == 0
    assert rows["00501"]["city_source"] == "zbp" and rows["00501"]["n_gov_sources"] == 1
    m = rows["09001"]
    assert m["n_gov_sources"] == 0 and m["is_military_prefix"] == 1 and m["city"] == "APO" and m["city_source"] == "v2"


def test_write_csv_and_summary():
    records = _records()
    rows = merge(records)
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "out.csv")
        write_csv(rows, path)
        with open(path, encoding="utf-8") as fh:
            got = list(csv.DictReader(fh))
    assert list(got[0]) == COLUMNS and len(got) == 3 and got[0]["zipcode"] == "00501"
    s = summarize(rows, records, {})
    assert s["zip_codes_total"] == 3 and s["zip_codes_in_any_government_source"] == 2 and s["zip_codes_only_in_v2"] == 1
    assert s["v2_coverage_by_type"]["MILITARY"] == {"in_v2": 1, "in_a_government_source": 0, "share": 0.0}
    assert s["not_in_v2"] == ["00501"]


def test_parse_years():
    assert _parse_years("2022") == [2022]
    assert _parse_years("2011-2013, 2022") == [2011, 2012, 2013, 2022]
