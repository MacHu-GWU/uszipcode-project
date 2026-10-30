# -*- coding: utf-8 -*-

"""
build.py: PK sets, reading the crawler outputs (B1-B3), the left join and the database files.
"""

import csv
import json
import os
import sqlite3

import pytest

from data_pipeline.database import build as build_mod
from data_pipeline.database import fetch
from data_pipeline.database.cli import main
from data_pipeline.database.core import ContractError, Field, Paths, PipelineError, PkSetError

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


def test_locked_database_gives_a_friendly_message(world, monkeypatch, capsys):
    def locked(src, dst):
        raise PermissionError(13, "The process cannot access the file")
    monkeypatch.setattr(os, "replace", locked)
    assert main(["build", "--pk-set", world.pk_csv], fields=world.fields, crawlers=world.crawlers, paths=world.paths) == 1
    err = capsys.readouterr().err
    assert err.strip() == ("cannot replace %s: close programs that have it open (Excel, DB Browser) and run again"
                           % os.path.join(world.paths.db_out_dir, "db_pks_fake.sqlite"))
