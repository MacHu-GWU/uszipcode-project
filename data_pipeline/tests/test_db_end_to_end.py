# -*- coding: utf-8 -*-

"""
End to end on fake worlds of several sizes: check -> crawl --all -> build -> refresh.
The numbers of PKs, Fields and crawlers are parameters, not constants of the code.
"""

import json
import sqlite3

import pytest

from data_pipeline.database import fetch
from data_pipeline.database.cli import main
from data_pipeline.database.core import SQL_TYPES

from fakes import FakeOpener, make_fake_world


def _run(world, *argv):
    return main(list(argv), fields=world.fields, crawlers=world.crawlers, paths=world.paths)


def _db_rows(path):
    con = sqlite3.connect(path)
    try:
        info = con.execute("PRAGMA table_info(zipcode_data)").fetchall()
        rows = [list(r) for r in con.execute("SELECT * FROM zipcode_data ORDER BY zipcode")]
    finally:
        con.close()
    return info, rows


def _read(path):
    with open(path, "rb") as fh:
        return fh.read()


@pytest.mark.parametrize("n_pks, n_fields, n_crawlers", [(1, 1, 1), (3, 5, 2), (30, 10, 4), (300, 64, 8)])
def test_end_to_end(tmp_path, monkeypatch, capsys, n_pks, n_fields, n_crawlers):
    world = make_fake_world(str(tmp_path / "world"), n_pks, n_fields, n_crawlers)
    opener = FakeOpener(world.served)
    monkeypatch.setattr(fetch, "urlopen", opener)

    assert _run(world, "check") == 0
    assert "%d Fields, %d crawlers" % (n_fields, n_crawlers) in capsys.readouterr().out

    # one request per crawler, then none: the downloads are cached
    assert _run(world, "crawl", "--all") == 0
    assert len(opener.calls) == n_crawlers
    assert _run(world, "crawl", "--all") == 0
    assert len(opener.calls) == n_crawlers

    assert _run(world, "build", "--pk-set", world.pk_csv) == 0
    stem = world.paths.db_out_dir + "/db_pks_fake"
    info, rows = _db_rows(stem + ".sqlite")
    assert [(c[1], c[2]) for c in info] == [("zipcode", "TEXT")] + [(f.name, SQL_TYPES[f.dtype]) for f in world.fields]
    assert info[0][3] == 1 and info[0][5] == 1  # NOT NULL, PRIMARY KEY
    assert len(rows) == n_pks and len(rows[0]) == 1 + n_fields
    assert rows == world.expected()

    with open(stem + "_coverage.json", encoding="utf-8") as fh:
        coverage = json.load(fh)
    assert (coverage["pk_set"], coverage["pks"], coverage["columns"]) == ("pks_fake", n_pks, 1 + n_fields)
    expected = world.expected()
    for i, f in enumerate(world.fields):
        c = coverage["fields"][f.name]
        non_null = sum(1 for r in expected if r[i + 1] is not None)
        assert c["crawler"] == "fake-%d" % (i % n_crawlers + 1)
        assert (c["non_null"], c["not_in_source"]) == (non_null, world.not_in_source(i))
        assert c["empty_in_source"] == n_pks - non_null - c["not_in_source"]
    for c in coverage["crawlers"].values():
        assert c["rows_outside_pk_set"] == 2  # 99001 and 99002; 00000 is skipped by the crawler
    assert world.pks[-1] in coverage["pks_without_any_value"]
    assert sum(coverage["pks_by_non_null_fields"].values()) == n_pks

    # a rebuild from the same crawler outputs gives the same bytes
    csv_bytes, cov_bytes = _read(stem + ".csv"), _read(stem + "_coverage.json")
    assert _run(world, "build", "--pk-set", world.pk_csv) == 0
    assert (_read(stem + ".csv"), _read(stem + "_coverage.json")) == (csv_bytes, cov_bytes)

    # fake-1's source changes: one refresh request, and only fake-1's columns change
    opener.served["https://fake.test/fake-1.csv"] = world.source_bytes(0, bump=1)
    assert _run(world, "crawl", "fake-1", "--refresh", "--force") == 0
    assert len(opener.calls) == n_crawlers + 1
    assert _run(world, "build", "--pk-set", world.pk_csv) == 0
    _, new_rows = _db_rows(stem + ".sqlite")
    assert new_rows == world.expected(bumps={0: 1})
    for i in range(n_fields):
        if i % n_crawlers != 0:
            assert [r[i + 1] for r in new_rows] == [r[i + 1] for r in rows]


def test_crawl_arguments(tmp_path, capsys):
    world = make_fake_world(str(tmp_path / "world"), 3, 5, 2)
    assert _run(world, "crawl") == 2
    assert _run(world, "crawl", "fake-1", "--all") == 2
    assert "exactly one of NAME or --all" in capsys.readouterr().err
    assert _run(world, "crawl", "fak-1") == 2
    assert "unknown crawler 'fak-1' (did you mean 'fake-1'?); known: fake-1, fake-2" in capsys.readouterr().err


def test_crawl_all_stops_at_first_failure(tmp_path, monkeypatch, capsys):
    world = make_fake_world(str(tmp_path / "world"), 3, 5, 2)
    served = dict(world.served)
    del served["https://fake.test/fake-1.csv"]
    opener = FakeOpener(served)
    monkeypatch.setattr(fetch, "urlopen", opener)
    assert _run(world, "crawl", "--all") == 1
    assert opener.urls == ["https://fake.test/fake-1.csv"]
    assert "fake-1: fake-1.csv: HTTP 404 from https://fake.test/fake-1.csv" in capsys.readouterr().err


def test_build_before_crawl_says_what_to_run(tmp_path, capsys):
    world = make_fake_world(str(tmp_path / "world"), 3, 5, 2)
    assert _run(world, "build", "--pk-set", world.pk_csv) == 1
    err = capsys.readouterr().err
    assert "[B1] crawler output missing" in err and "run: mise run crawler-fake-1" in err
    assert "Traceback" not in err
