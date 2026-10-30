# -*- coding: utf-8 -*-

"""
crawl.py: the output contract (D1-D6), the crawler output files and run_crawler().
"""

import os

import pytest

from data_pipeline.database import fetch
from data_pipeline.database.core import ContractError, Crawler, Download, Field, Paths
from data_pipeline.database.crawl import check_rows, read_meta, read_output, run_crawler, write_output

from fakes import FakeOpener

FIELDS = [Field("n", int, "a count"), Field("x", float, "a share"), Field("s", str, "a name")]
CATALOG = {f.name: f for f in FIELDS}
URL = "https://data.test/src.csv"


def _crawler(parse=lambda files: [], name="src"):
    return Crawler(name, ("n", "x", "s"), (Download("src.csv", URL),), parse)


def _check(rows):
    return check_rows(_crawler(), CATALOG, rows)


def _error(rows) -> str:
    with pytest.raises(ContractError) as e:
        _check(rows)
    return str(e.value)


GOOD = ("10001", {"n": 1, "x": 0.5, "s": "a"})


@pytest.mark.parametrize("rule, rows, text", [
    ("D1", [GOOD, ("10001", {"n": 2})], "zipcode 10001 appears again (first at row 1)"),
    ("D1", [("501", {"n": 1, "x": 1.0, "s": "a"}), ("00501", {"n": 2})], "zipcode 00501 appears again"),
    ("D2", [GOOD, ("20037", {"n": 1, "zz": 2})], "row 2, zipcode 20037: 'zz' is not a Field of crawler 'src'"),
    ("D3", [GOOD, ("20037", {"n": "12"})], "row 2, zipcode 20037, field n: '12' is not an int"),
    ("D4", [("10001", {"n": 1, "x": 0.5}), ("20037", {"n": 2, "s": " "})], "Field 's' is NULL in every row"),
    ("D5", [], "parse() returned no usable rows (0 rows, 0 skipped keys)"),
    ("D5", [("00000", {"n": 1}), ("ABC", {"n": 2})], "parse() returned no usable rows (2 rows, 2 skipped keys)"),
    ("D6", [GOOD, ("20037", {"x": float("nan")})], "field x: nan is not a finite number"),
    ("D6", [GOOD, ("20037", {"x": float("inf")})], "field x: inf is not a finite number"),
])
def test_each_rule(rule, rows, text):
    message = _error(rows)
    assert message.startswith("crawler 'src': output contract failed:")
    assert any(line.strip().startswith("[%s]" % rule) and text in line for line in message.splitlines()), message


def test_first_20_errors_are_listed():
    rows = [GOOD] + [("%05d" % (20000 + i), {"n": 1, "bad": i}) for i in range(21)]
    lines = _error(rows).splitlines()
    assert lines[0] == "crawler 'src': output contract failed: 21 problem(s)"
    assert len(lines) == 1 + 20 + 1 and lines[-1].strip() == "... and 1 more"


def test_keys_are_normalized_and_non_zips_skipped():
    records, stats = _check([("501", {"n": 1}), (" 20037 ", {"n": 2}), ("00000", {"n": 3}), ("ABC", {"n": 4}),
                             ("10001", {"x": 1.5, "s": "b"})])
    assert [z for z, _ in records] == ["00501", "10001", "20037"]
    assert stats["skipped_keys"] == 2 and stats["skipped_examples"] == ["00000", "ABC"]
    assert stats["rows"] == 3 and stats["non_null"] == {"n": 2, "x": 1, "s": 1}


@pytest.mark.parametrize("value", [True, "3", 3.0])
def test_int_rejects_bool_str_and_float(value):
    assert "[D3]" in _error([GOOD, ("20037", {"n": value})])


@pytest.mark.parametrize("field, value", [("x", "0.5"), ("x", False), ("s", 3)])
def test_float_and_str_types(field, value):
    assert "[D3]" in _error([GOOD, ("20037", {field: value})])


def test_output_files_are_exact_and_stable(tmp_path):
    rows = [("20037", {"n": 0, "x": 3, "s": "  b "}), ("10001", {"n": None, "x": 0.1, "s": "a"}),
            ("501", {"n": 7, "x": None, "s": "c,d"})]
    records, stats = _check(rows)
    assert records == [("00501", [7, None, "c,d"]), ("10001", [None, 0.1, "a"]), ("20037", [0, 3.0, "b"])]
    out = str(tmp_path / "out")
    path = write_output(_crawler(), records, dict(stats, crawler="src"), out)
    with open(path, "rb") as fh:
        first = fh.read()
    # NULL is an empty cell, 0 stays 0, an int in a float Field is written 3.0, no BOM, \n endings
    assert first == b'zipcode,n,x,s\n00501,7,,"c,d"\n10001,,0.1,a\n20037,0,3.0,b\n'
    write_output(_crawler(), records, dict(stats, crawler="src"), out)
    with open(path, "rb") as fh:
        assert fh.read() == first
    assert read_output(_crawler(), CATALOG, out) == {
        "00501": {"n": 7, "x": None, "s": "c,d"}, "10001": {"n": None, "x": 0.1, "s": "a"},
        "20037": {"n": 0, "x": 3.0, "s": "b"}}
    assert read_meta(_crawler(), out)["non_null"] == {"n": 2, "x": 2, "s": 3}
    assert sorted(os.listdir(out)) == ["src.csv", "src.json"]


def _parse_ok(files):
    yield "10001", {"n": 1, "x": 0.5, "s": "a"}
    yield "20037", {"n": 2, "x": None, "s": "b"}


def _parse_bad(files):
    yield "10001", {"n": "1"}


def _parse_crash(files):
    raise KeyError("P1_001N")


def test_run_crawler_writes_output_and_keeps_it_on_failure(tmp_path, monkeypatch):
    paths = Paths.under(str(tmp_path))
    opener = FakeOpener({URL: b"anything"})
    monkeypatch.setattr(fetch, "urlopen", opener)
    summary = run_crawler(_crawler(_parse_ok), FIELDS, paths)
    assert (summary["crawler"], summary["requests"], summary["files"], summary["rows"]) == ("src", 1, 1, 2)
    csv_path = os.path.join(paths.crawler_out_dir, "src.csv")
    with open(csv_path, "rb") as fh:
        good = fh.read()
    meta = read_meta(_crawler(), paths.crawler_out_dir)
    assert meta["fields"] == [{"name": "n", "dtype": "int"}, {"name": "x", "dtype": "float"}, {"name": "s", "dtype": "str"}]
    assert meta["downloads"]["src.csv"]["url"] == URL
    assert set(meta) == {"crawler", "fields", "rows", "skipped_keys", "skipped_examples", "non_null", "downloads"}

    with pytest.raises(ContractError) as e:
        run_crawler(_crawler(_parse_bad), FIELDS, paths)
    assert "[D3]" in str(e.value)
    with pytest.raises(ContractError) as e:
        run_crawler(_crawler(_parse_crash), FIELDS, paths)
    assert "crawler 'src': parse() failed: KeyError: 'P1_001N'" in str(e.value)
    with open(csv_path, "rb") as fh:
        assert fh.read() == good
    assert len(opener.calls) == 1  # the failed runs used the cache

    # same cache, same output bytes (no run timestamp in the files)
    json_path = os.path.join(paths.crawler_out_dir, "src.json")
    with open(json_path, "rb") as fh:
        meta_bytes = fh.read()
    run_crawler(_crawler(_parse_ok), FIELDS, paths)
    with open(json_path, "rb") as fh:
        assert fh.read() == meta_bytes
