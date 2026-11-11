# -*- coding: utf-8 -*-

"""
build.py: PK sets, reading the crawler outputs (B1-B3), the left join and the database files.
"""

import csv
import dataclasses
import json
import os
import sqlite3
import zlib

import pytest

from uszipcode.data import build as build_mod
from uszipcode.data import fetch
from uszipcode.data.checks import task_command
from uszipcode.data.cli import main
from uszipcode.data.core import ContractError, Crawler, Download, Field, Paths, PipelineError, PkSetError

from fakes import FakeOpener, make_fake_world


# ------------------------------------------------------------------------------------------ PK sets
def _paths(tmp_path):
    return Paths.under(str(tmp_path))


def _write(path, text):
    os.makedirs(os.path.dirname(str(path)), exist_ok=True)
    with open(str(path), "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    return str(path)


def test_demo_pk_set(tmp_path):
    assert build_mod.load_pk_set("demo", _paths(tmp_path)) == ("demo", ["10001", "20013", "20037"])


def test_full_pk_set(tmp_path):
    paths = _paths(tmp_path)
    with pytest.raises(PkSetError) as e:
        build_mod.load_pk_set("full", paths)
    assert str(e.value) == "%s not found; run: mise run zipcode-universe" % paths.universe_csv
    _write(paths.universe_csv, "zipcode,city\n20037,WASHINGTON\n00501,HOLTSVILLE\n")
    assert build_mod.load_pk_set("full", paths) == ("full", ["00501", "20037"])


def test_pk_set_from_a_csv_file(tmp_path):
    path = _write(tmp_path / "sets" / "my-set_1.csv", "state,zipcode\nDC,20037\nNY,10001\n\n")
    assert build_mod.load_pk_set(path, _paths(tmp_path)) == ("my-set_1", ["10001", "20037"])
    path = _write(tmp_path / "sets" / "excel.csv", "﻿zipcode\r\n20037\r\n")  # saved by Excel
    assert build_mod.load_pk_set(path, _paths(tmp_path)) == ("excel", ["20037"])


@pytest.mark.parametrize("name, text, message", [
    ("bad.csv", "zipcode\n20037\n2003\n", "PK set 'bad': line 3: '2003' is not a 5-digit ZIP"),
    ("bad.csv", "zipcode\n00000\n", "PK set 'bad': line 2: '00000' is not a 5-digit ZIP"),
    ("dup.csv", "zipcode\n20037\n10001\n10002\n20037\n", "PK set 'dup': duplicate ZIP '20037' (lines 2 and 5)"),
    ("nocol.csv", "zip\n20037\n", "PK set 'nocol' has no 'zipcode' column"),
    ("empty.csv", "zipcode\n", "PK set 'empty' is empty"),
    ("my set.csv", "zipcode\n20037\n", "PK set file name 'my set' may only use A-Z a-z 0-9 _ -"),
])
def test_pk_set_errors(tmp_path, name, text, message):
    path = _write(tmp_path / name, text)
    with pytest.raises(PkSetError) as e:
        build_mod.load_pk_set(path, _paths(tmp_path))
    assert str(e.value) == message


@pytest.mark.parametrize("name", ["demo", "full"])
def test_a_pk_set_file_cannot_take_a_built_in_name(tmp_path, name):
    path = _write(tmp_path / (name + ".csv"), "zipcode\n20037\n")
    with pytest.raises(PkSetError) as e:
        build_mod.load_pk_set(path, _paths(tmp_path))
    assert str(e.value) == "PK set file %r has the name of the built-in set %r: rename the file" % (path, name)


def test_a_pk_set_file_cannot_take_the_name_of_a_simple_release(tmp_path):
    path = _write(tmp_path / "east_simple.csv", "zipcode\n20037\n")  # db_east_simple.sqlite: the simple release of "east"
    with pytest.raises(PkSetError) as e:
        build_mod.load_pk_set(path, _paths(tmp_path))
    assert str(e.value) == "PK set file name 'east_simple' ends with '_simple', the name of a simple release: rename the file"


def test_unknown_pk_set(tmp_path):
    with pytest.raises(PkSetError) as e:
        build_mod.load_pk_set("nope", _paths(tmp_path))
    assert "is not 'demo', 'full' or an existing CSV file" in str(e.value)


def test_demo_pks_are_in_the_committed_universe():
    with open(Paths.default().universe_csv, encoding="utf-8", newline="") as fh:
        rows = {r["zipcode"]: r for r in csv.DictReader(fh)}
    assert all(pk in rows for pk in build_mod.DEMO_PKS)
    assert rows["20013"]["in_census_zcta"] == "0"  # a PO box: no Census values
    assert rows["10001"]["in_census_zcta"] == rows["20037"]["in_census_zcta"] == "1"


# ----------------------------------------------------------------------------------------- the join
def test_assemble_is_a_left_join():
    fields = [Field("a", int, "A"), Field("b", str, "B"), Field("c", float, "C")]
    owner = {"a": "one", "b": "two", "c": "one"}
    outputs = {"one": {"10001": {"a": 1, "c": None}, "99001": {"a": 9, "c": 9.0}},
               "two": {"20037": {"b": "x"}}}
    assert build_mod.assemble(["10001", "20013", "20037"], fields, owner, outputs) == [
        ["10001", 1, None, None], ["20013", None, None, None], ["20037", None, "x", None]]


@pytest.fixture
def world(tmp_path, monkeypatch):
    w = make_fake_world(str(tmp_path / "world"), 3, 5, 2)
    monkeypatch.setattr(fetch, "urlopen", FakeOpener(w.served))
    assert main(["crawl", "--all"], fields=w.fields, crawlers=w.crawlers, paths=w.paths) == 0
    return w


def _build(w, pk_set=None):
    return build_mod.build(w.fields, w.crawlers, w.paths, pk_set=pk_set or w.pk_csv)


def test_database_files_and_types(world):
    coverage = _build(world)
    assert coverage["files"]["sqlite"].endswith("db_pks_fake.sqlite")
    con = sqlite3.connect(coverage["files"]["sqlite"])
    try:
        names = [r[1] for r in con.execute("PRAGMA table_info(zipcode_data)")]
        types = con.execute("SELECT %s FROM zipcode_data WHERE zipcode = '00538'"
                            % ", ".join("typeof(%s)" % n for n in names)).fetchone()
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
    finally:
        con.close()
    assert tables == ["zipcode_data"]
    # PK k=1 (00538): f01 int, f02 float, f03 str, f04 int (blank: (1+3) % 4 == 0), f05 float
    assert list(types) == ["text", "integer", "real", "text", "null", "real"]
    with open(coverage["files"]["csv"], encoding="utf-8") as fh:
        assert fh.readline() == "zipcode,f01,f02,f03,f04,f05\n"
    with open(coverage["files"]["sqlite"][:-len(".sqlite")] + "_coverage.json", encoding="utf-8") as fh:
        saved = json.load(fh)
    assert saved["files"] == {"sqlite": "db_pks_fake.sqlite", "csv": "db_pks_fake.csv"}
    assert saved["crawlers"]["fake-1"]["source_rows"] == saved["crawlers"]["fake-1"]["rows_in_pk_set"] + 2
    assert saved["crawlers"]["fake-1"]["downloads"]["fake-1.csv"]["url"] == "https://fake.test/fake-1.csv"


def test_switching_pk_sets_downloads_nothing(world, monkeypatch, tmp_path):
    def no_download(*args, **kwargs):
        raise AssertionError("build must not download")
    monkeypatch.setattr(fetch, "urlopen", no_download)
    other = _write(tmp_path / "two.csv", "zipcode\n00501\n99001\n")
    coverage = _build(world, other)
    assert (coverage["pk_set"], coverage["pks"]) == ("two", 2)
    # fake-1 has 00538, 99001, 99002 (00501 is a gap); fake-2 has 00501, 00538, 99001, 99002
    assert coverage["crawlers"]["fake-1"] | {"downloads": None} == {
        "source_rows": 3, "rows_in_pk_set": 1, "rows_outside_pk_set": 2, "downloads": None}
    assert coverage["crawlers"]["fake-2"] | {"downloads": None} == {
        "source_rows": 4, "rows_in_pk_set": 2, "rows_outside_pk_set": 2, "downloads": None}


def test_missing_output_b1(world):
    os.remove(os.path.join(world.paths.crawler_out_dir, "fake-2.json"))
    with pytest.raises(PipelineError) as e:
        _build(world)
    assert str(e.value) == "[B1] crawler output missing: %s; run: mise run crawler-fake-2" % os.path.join(
        world.paths.crawler_out_dir, "fake-2.json")


def test_stale_output_b2(world):
    path = os.path.join(world.paths.crawler_out_dir, "fake-1.csv")
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    lines[0] = "zipcode,f01,f03"
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(lines))
    with pytest.raises(ContractError) as e:
        _build(world)
    assert str(e.value) == ('[B2] crawler output %s is stale: its header is "zipcode,f01,f03" but fake-1 claims '
                            '"f01,f03,f05"; run: mise run crawler-fake-1' % path)


def test_other_downloads_b2(world):
    moved = Download("fake-1.csv", "https://fake.test/2027/fake-1.csv", magic=b"zipcode,")
    crawlers = [dataclasses.replace(world.crawlers[0], downloads=(moved,))] + world.crawlers[1:]
    with pytest.raises(ContractError) as e:  # as after a new year in the crawler, before it ran again
        build_mod.build(world.fields, crawlers, world.paths, pk_set=world.pk_csv)
    assert str(e.value) == ("[B2] crawler output %s is stale: fake-1 declares other downloads now (fake-1.csv); "
                            "run: mise run crawler-fake-1" % os.path.join(world.paths.crawler_out_dir, "fake-1.csv"))


def test_missing_history_output_b1(world):
    yearly = Field("h", int, "a yearly count", extract=lambda row: row["h"])
    hist = Crawler("fake-history", ("h",), (Download("hist.csv", "https://fake.test/hist.csv"),), lambda files: [],
                   history=True)
    with open(world.paths.mise_toml, "a", encoding="utf-8") as fh:
        fh.write('[tasks.crawler-fake-history]\nrun = "%s"\n' % task_command("fake-history"))
    with pytest.raises(PipelineError) as e:  # the main crawlers ran, the history crawler did not
        build_mod.build(world.fields, world.crawlers + [hist], world.paths, pk_set=world.pk_csv, history_fields=[yearly])
    assert str(e.value) == "[B1] crawler output missing: %s; run: mise run crawler-fake-history" % os.path.join(
        world.paths.crawler_out_dir, "fake-history.csv")


def test_empty_line_b3(world):
    path = os.path.join(world.paths.crawler_out_dir, "fake-2.csv")
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(lines[:1] + [""] + lines[1:]))
    with pytest.raises(ContractError) as e:
        _build(world)
    assert str(e.value) == "[B3] %s line 2: not a valid row: []" % path


def test_bad_cell_b3(world):
    path = os.path.join(world.paths.crawler_out_dir, "fake-2.csv")
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    lines[1] = lines[1].split(",")[0] + ",abc,1.5"
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(lines))
    with pytest.raises(ContractError) as e:
        _build(world)
    assert str(e.value) == "[B3] %s line 2: 'abc' is not a valid float for field f02" % path


def _ratio_field(name, top, bottom):
    def extract(row):
        return None if row[top] is None or not row[bottom] else row[top] / row[bottom]
    return Field(name, float, "%s per %s" % (top, bottom), extract=extract, inputs=(top, bottom))


def test_derived_fields_are_computed_after_the_join(world, tmp_path):
    # f01 is an int of fake-1, f02 a float of fake-2: a derived Field joins two crawlers
    fields = list(world.fields) + [_ratio_field("f01_per_f02", "f01", "f02"), _ratio_field("twice", "f01_per_f02", "f02")]
    coverage = build_mod.build(fields, world.crawlers, world.paths, pk_set=world.pk_csv)
    con = sqlite3.connect(coverage["files"]["sqlite"])
    try:
        rows = con.execute("SELECT zipcode, f01, f02, f01_per_f02, twice FROM zipcode_data ORDER BY zipcode").fetchall()
        assert con.execute("SELECT typeof(f01_per_f02) FROM zipcode_data WHERE f01_per_f02 IS NOT NULL").fetchone() == ("real",)
    finally:
        con.close()
    for zipcode, f01, f02, derived, twice in rows:
        expected = None if f01 is None or not f02 else f01 / f02
        assert derived == expected and twice == (None if expected is None or not f02 else expected / f02), zipcode
    c = coverage["fields"]["f01_per_f02"]
    assert c["crawler"] == "derived" and c["derived_from"] == ["f01", "f02"]
    assert c["non_null"] == sum(1 for r in rows if r[3] is not None)
    assert c["not_in_source"] == sum(1 for r in rows if r[1] is None or r[2] is None)


def test_a_failing_derived_field_stops_the_build(world):
    broken = Field("broken", int, "always fails", extract=lambda row: 1 / 0, inputs=("f01",))
    with pytest.raises(ContractError) as e:
        build_mod.build(list(world.fields) + [broken], world.crawlers, world.paths, pk_set=world.pk_csv)
    assert "derived Fields failed: 3 problem(s)" in str(e.value)
    assert "[B4] derived Field broken, zipcode 00501: ZeroDivisionError: division by zero" in str(e.value)


def test_history_is_one_json_column_per_history_field(world, monkeypatch):
    yearly = Field("h", int, "a yearly count", extract=lambda row: int(row["h"]) if row["h"] else None)

    def parse(files):
        with open(files["hist.csv"], encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                yield row["zipcode"], row

    hist = Crawler("fake-history", ("h",), (Download("hist.csv", "https://fake.test/hist.csv", magic=b"zipcode,"),),
                   parse, history=True)
    # 00501: two years, written out of order; 00538: a year without a value; 99001: outside the PK set
    body = "zipcode,year,h\n00501,2012,2\n00501,2011,1\n00538,2012,\n99001,2012,9\n"
    monkeypatch.setattr(fetch, "urlopen", FakeOpener({"https://fake.test/hist.csv": body.encode()}))
    with open(world.paths.mise_toml, "a", encoding="utf-8") as fh:
        fh.write('[tasks.crawler-fake-history]\nrun = "%s"\n' % task_command("fake-history"))
    crawlers = world.crawlers + [hist]
    kw = dict(fields=world.fields, crawlers=crawlers, paths=world.paths, history_fields=[yearly])
    assert main(["crawl", "fake-history"], **kw) == 0
    coverage = build_mod.build(world.fields, crawlers, world.paths, pk_set=world.pk_csv, history_fields=[yearly])

    con = sqlite3.connect(coverage["files"]["sqlite"])
    try:
        rows = dict(con.execute("SELECT zipcode, h_by_year FROM zipcode_data"))
        info = con.execute("PRAGMA table_info(zipcode_data)").fetchall()
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
    finally:
        con.close()
    assert tables == ["zipcode_data"]  # no second table
    assert rows == {"00501": '{"2011":1,"2012":2}', "00538": None, world.pks[2]: None}
    assert (info[-1][1], info[-1][2]) == ("h_by_year", "TEXT")
    assert len(info) == coverage["columns"] == 1 + len(world.fields) + 1
    with open(coverage["files"]["csv"], encoding="utf-8", newline="") as fh:
        in_csv = {r["zipcode"]: r["h_by_year"] for r in csv.DictReader(fh)}
    assert in_csv == {"00501": '{"2011":1,"2012":2}', "00538": "", world.pks[2]: ""}
    h = coverage["history"]
    assert (h["pks"], h["years"]) == (1, [2011, 2012])
    assert h["fields"]["h"] == {"column": "h_by_year", "crawler": "fake-history", "pks": 1, "values": 2,
                                "years": [2011, 2012]}
    assert {k: v for k, v in h["crawlers"]["fake-history"].items() if k != "downloads"} == {
        "source_rows": 4, "rows_in_pk_set": 3, "rows_outside_pk_set": 1}
    assert "fake-history" not in coverage["crawlers"]
    assert "History: 1 JSON columns, 1 PKs with a value, years 2011-2012" in build_mod.describe_coverage(coverage)


def test_history_json():
    assert build_mod.history_json({2012: 14304, 2011: 13642}) == '{"2011":13642,"2012":14304}'
    assert build_mod.history_json({2020: 0.5}) == '{"2020":0.5}'
    assert build_mod.history_json({}) is None


def test_a_compressed_field_is_a_zlib_blob_in_sqlite_and_text_in_the_csv(world):
    fields = [dataclasses.replace(f, compressed=f.name == "f03") for f in world.fields]  # f03 is a str Field
    coverage = build_mod.build(fields, world.crawlers, world.paths, pk_set=world.pk_csv)
    con = sqlite3.connect(coverage["files"]["sqlite"])
    try:
        stored = dict(con.execute("SELECT zipcode, f03 FROM zipcode_data"))
        declared = {r[1]: r[2] for r in con.execute("PRAGMA table_info(zipcode_data)")}
    finally:
        con.close()
    with open(coverage["files"]["csv"], encoding="utf-8", newline="") as fh:
        text = {r["zipcode"]: r["f03"] for r in csv.DictReader(fh)}
    assert declared["f03"] == "BLOB" and any(text.values())
    for zipcode, blob in stored.items():
        assert (zlib.decompress(blob).decode("utf-8") if blob is not None else "") == text[zipcode]


def test_a_large_pk_set_gets_no_csv(world, monkeypatch):
    csv_path = _build(world)["files"]["csv"]
    assert os.path.exists(csv_path)
    monkeypatch.setattr(build_mod, "CSV_MAX_ROWS", 2)  # the set has 3 PKs
    coverage = _build(world)
    assert list(coverage["files"]) == ["sqlite"]
    assert not os.path.exists(csv_path)  # the CSV of the earlier build would be stale


def _table(path):
    con = sqlite3.connect(path)
    try:
        declared = [(r[1], r[2], r[5]) for r in con.execute("PRAGMA table_info(zipcode_data)")]
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
        return tables, declared, con.execute("SELECT * FROM zipcode_data ORDER BY zipcode").fetchall()
    finally:
        con.close()


def test_the_simple_release_is_a_part_of_the_columns(world, capsys):
    # f02 (float), f03 (str, compressed) and f05 are simple; the history Field is never part of it
    fields = [dataclasses.replace(f, simple=f.name in ("f02", "f03", "f05"), compressed=f.name == "f03")
              for f in world.fields]
    args = ["build", "--pk-set", world.pk_csv]
    assert main(args, fields=fields, crawlers=world.crawlers, paths=world.paths) == 0
    out = capsys.readouterr().out
    assert "Simple release: 3 rows x 4 columns (zipcode and 3 Fields)" in out
    stem = os.path.join(world.paths.db_out_dir, "db_pks_fake")
    wrote = out.splitlines()[-1]
    assert wrote.startswith("wrote ") and [os.path.basename(p) for p in wrote[len("wrote "):].replace(" and ", ", ").split(", ")] \
        == ["db_pks_fake.sqlite", "db_pks_fake_simple.sqlite", "db_pks_fake.csv", "db_pks_fake_coverage.json"]

    tables, declared, rows = _table(stem + "_simple.sqlite")
    assert tables == ["zipcode_data"]
    assert declared == [("zipcode", "TEXT", 1), ("f02", "REAL", 0), ("f03", "BLOB", 0), ("f05", "REAL", 0)]
    _, full_declared, full_rows = _table(stem + ".sqlite")
    keep = [i for i, (name, _, _) in enumerate(full_declared) if name in ("zipcode", "f02", "f03", "f05")]
    assert rows == [tuple(row[i] for i in keep) for row in full_rows]  # the same values, the blob included
    with open(stem + "_coverage.json", encoding="utf-8") as fh:
        saved = json.load(fh)
    assert saved["simple"] == {"columns": 4, "fields": ["f02", "f03", "f05"]}
    assert saved["files"] == {"sqlite": "db_pks_fake.sqlite", "simple_sqlite": "db_pks_fake_simple.sqlite",
                              "csv": "db_pks_fake.csv"}


def test_without_simple_fields_there_is_no_simple_release(world):
    fields = [dataclasses.replace(f, simple=f.name == "f01") for f in world.fields]
    simple_path = build_mod.build(fields, world.crawlers, world.paths, pk_set=world.pk_csv)["files"]["simple_sqlite"]
    assert os.path.exists(simple_path)
    coverage = _build(world)  # no Field of the fake world is simple
    assert "simple" not in coverage and list(coverage["files"]) == ["sqlite", "csv"]
    assert not os.path.exists(simple_path)  # the file of the earlier build would be stale
    assert "Simple release" not in build_mod.describe_coverage(coverage)


def test_simple_table():
    fields = [Field("a", int, "a", simple=True), Field("b", str, "b"), Field("c", float, "c", simple=True)]
    kept, rows = build_mod.simple_table(fields, [["10001", 1, "x", 0.5], ["20013", None, None, None]])
    assert [f.name for f in kept] == ["a", "c"]
    assert rows == [["10001", 1, 0.5], ["20013", None, None]]


def test_locked_database_gives_a_friendly_message(world, monkeypatch, capsys):
    def locked(src, dst):
        raise PermissionError(13, "The process cannot access the file")
    monkeypatch.setattr(os, "replace", locked)
    assert main(["build", "--pk-set", world.pk_csv], fields=world.fields, crawlers=world.crawlers, paths=world.paths) == 1
    err = capsys.readouterr().err
    assert err.strip() == ("cannot replace %s: close programs that have it open (Excel, DB Browser) and run again"
                           % os.path.join(world.paths.db_out_dir, "db_pks_fake.sqlite"))
