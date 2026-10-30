# -*- coding: utf-8 -*-

"""
Registry checks: every rule F1-F5, C1-C8, K1-K3 and M0-M2 fails on its own example,
and the real registry passes.
"""

import dataclasses

import pytest

from data_pipeline.database.cli import main
from data_pipeline.database.core import Crawler, Download, Field, Paths, RegistryError, Secret
from data_pipeline.database.fields import FIELDS
from data_pipeline.database.registry import CRAWLERS, require_valid, task_command, validate


def test_real_registry_is_valid():
    assert validate(FIELDS, CRAWLERS, Paths.default().mise_toml) == []


def test_check_prints_the_catalog(capsys):
    assert main(["check"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("5 Fields, 2 crawlers, every Field claimed once, mise tasks match.")
    for f in FIELDS:
        assert any(line.split()[:2] == [f.name, f.dtype.__name__] for line in out.splitlines())
    assert "population" in out and "census-dhc" in out and "census-gazetteer" in out


# ------------------------------------------------------------------------------- one rule at a time
def _parse(files):
    return []


def _download(name="a.csv", url=None, **kw):
    return Download(name, url or "https://data.test/" + name, **kw)


def _crawler(name="src-a", fields=("a", "b"), downloads=None):
    return Crawler(name, tuple(fields), tuple(downloads if downloads is not None else (_download(name + ".csv"),)), _parse)


BASE_FIELDS = (Field("a", int, "A count"), Field("b", float, "B share"))
SECRET = dict(env="FAKE_KEY", file="~/.fake_key", signup_url="https://signup.test/")


def _mise(names):
    return "".join('[tasks.crawler-%s]\nrun = "%s"\n' % (n, task_command(n)) for n in names)


# rule id, expected text, Fields, crawlers, mise.toml text (None: tasks for every crawler)
CASES = [
    ("F1", "Field name 'Pop' is not snake_case", BASE_FIELDS + (Field("Pop", int, "x"),),
     [_crawler(fields=("a", "b", "Pop"))], None),
    ("F2", "Field name 'zipcode' is reserved for the primary key", BASE_FIELDS + (Field("zipcode", str, "x"),),
     [_crawler(fields=("a", "b", "zipcode"))], None),
    ("F3", "Field 'a' is defined twice in FIELDS: keep one.", BASE_FIELDS + (Field("a", int, "again"),),
     [_crawler()], None),
    ("F4", "Field 'c' has dtype bool: use int, float or str.", BASE_FIELDS + (Field("c", bool, "flag"),),
     [_crawler(fields=("a", "b", "c"))], None),
    ("F5", "Field 'c' has an empty description", BASE_FIELDS + (Field("c", int, "  "),),
     [_crawler(fields=("a", "b", "c"))], None),
    ("C1", "Crawler name 'Src_A' is not kebab-case", BASE_FIELDS, [_crawler("Src_A")], None),
    ("C1", "Crawler name '%s' is not kebab-case" % ("a" * 31), BASE_FIELDS, [_crawler("a" * 31)], None),
    ("C2", "Crawler name 'src-a' is used 2 times: names must be unique.", BASE_FIELDS,
     [_crawler(fields=("a",)), _crawler(fields=("b",), downloads=(_download("b.csv"),))], None),
    ("C3", "Crawler 'src-b' claims no Fields: add at least one.", BASE_FIELDS,
     [_crawler(), _crawler("src-b", fields=())], None),
    ("C4", "Crawler 'src-a' declares 0 downloads (allowed 1 to 100): a crawler downloads whole files, never one request per ZIP.",
     BASE_FIELDS, [_crawler(downloads=())], None),
    ("C4", "Crawler 'src-a' declares 101 downloads", BASE_FIELDS,
     [_crawler(downloads=[_download("f%d.csv" % i) for i in range(101)])], None),
    ("C5", "download filename 'a b.csv' must be 1-60 characters", BASE_FIELDS,
     [_crawler(downloads=(_download("a b.csv", "https://data.test/ab.csv"),))], None),
    ("C5", "download filename 'a.csv' is used 2 times", BASE_FIELDS,
     [_crawler(downloads=(_download("a.csv"), _download("a.csv", "https://data.test/other.csv")))], None),
    ("C6", "URL http://data.test/a.csv must start with https://.", BASE_FIELDS,
     [_crawler(downloads=(_download("a.csv", "http://data.test/a.csv"),))], None),
    ("C6", "has a api_key parameter: put the secret in Download.secret", BASE_FIELDS,
     [_crawler(downloads=(_download("a.csv", "https://data.test/a.csv?get=x&api_key=123"),))], None),
    ("C7", "must set exactly one of query_param or bearer", BASE_FIELDS,
     [_crawler(downloads=(_download(secret=Secret(**SECRET, query_param="key", bearer=True)),))], None),
    ("C7", "must set exactly one of query_param or bearer", BASE_FIELDS,
     [_crawler(downloads=(_download(secret=Secret(**SECRET)),))], None),
    ("C7", "the Secret file '/etc/key' must be in the home folder", BASE_FIELDS,
     [_crawler(downloads=(_download(secret=Secret(**dict(SECRET, file="/etc/key"), bearer=True)),))], None),
    ("C8", "URL https://data.test/a.csv is downloaded by both 'src-a' and 'src-b': one source, one crawler.", BASE_FIELDS,
     [_crawler(fields=("a",), downloads=(_download("a.csv"),)),
      _crawler("src-b", fields=("b",), downloads=(_download("a.csv"),))], None),
    ("K1", "Crawler 'src-a' claims 'populaton', which is not in FIELDS (did you mean 'population'?)",
     (Field("population", int, "people"),), [_crawler(fields=("populaton", "population"))], None),
    ("K2", "Field 'a' is claimed 2 times (src-a, src-b): exactly one crawler may claim it.", BASE_FIELDS,
     [_crawler(), _crawler("src-b", fields=("a",))], None),
    ("K3", "Field 'c' is not claimed by any crawler: add it to one crawler's fields.",
     BASE_FIELDS + (Field("c", str, "C name"),), [_crawler()], None),
    ("M0", "mise.toml not found at", BASE_FIELDS, [_crawler()], "<missing>"),
    ("M0", "mise.toml is not valid TOML", BASE_FIELDS, [_crawler()], "[tasks.crawler-src-a\n"),
    ("M1", "Crawler 'src-a' has no mise task: add to mise.toml\n[tasks.crawler-src-a]\nrun = \"%s\"" % task_command("src-a"),
     BASE_FIELDS, [_crawler()], "[tasks.pipeline-check]\nrun = \"x\"\n"),
    ("M1", "mise task 'crawler-src-a' runs 'python -m data_pipeline.database crawl src_a': expected \"%s\"." % task_command("src-a"),
     BASE_FIELDS, [_crawler()], '[tasks.crawler-src-a]\nrun = "python -m data_pipeline.database crawl src_a"\n'),
    ("M2", "mise task 'crawler-old' has no crawler named 'old': remove the task or register the crawler.",
     BASE_FIELDS, [_crawler()], _mise(["src-a", "old"])),
]


@pytest.mark.parametrize("rule, text, fields, crawlers, mise", CASES, ids=["%s-%d" % (c[0], i) for i, c in enumerate(CASES)])
def test_each_rule(tmp_path, rule, text, fields, crawlers, mise):
    path = tmp_path / "mise.toml"
    if mise != "<missing>":
        path.write_text(_mise([c.name for c in crawlers]) if mise is None else mise, encoding="utf-8")
    problems = validate(list(fields), crawlers, str(path))
    assert any(p.startswith("[%s] " % rule) and text in p for p in problems), problems


def test_the_valid_base_has_no_problem(tmp_path):
    path = tmp_path / "mise.toml"
    path.write_text(_mise(["src-a"]), encoding="utf-8")
    assert validate(list(BASE_FIELDS), [_crawler()], str(path)) == []
    assert validate(list(BASE_FIELDS), [_crawler()], None) == []  # mise.toml not checked


def test_all_problems_are_reported_together(tmp_path):
    path = tmp_path / "mise.toml"
    path.write_text("", encoding="utf-8")
    fields = list(BASE_FIELDS) + [Field("housing_units", int, "units")]
    with pytest.raises(RegistryError) as e:
        require_valid(fields, [_crawler()], str(path))
    assert [p[:4] for p in e.value.problems] == ["[K3]", "[M1]"]
    assert str(e.value).splitlines() == [
        "registry check failed: 2 problem(s)",
        "  1. [K3] Field 'housing_units' is not claimed by any crawler: add it to one crawler's fields.",
        "  2. [M1] Crawler 'src-a' has no mise task: add to mise.toml",
        "       [tasks.crawler-src-a]",
        '       run = "python -m data_pipeline.database crawl src-a"',
    ]


def test_check_fails_with_exit_code_2(tmp_path, capsys):
    paths = dataclasses.replace(Paths.under(str(tmp_path)), mise_toml=str(tmp_path / "mise.toml"))
    (tmp_path / "mise.toml").write_text(_mise(["census-gazetteer"]), encoding="utf-8")
    assert main(["check"], paths=paths) == 2
    err = capsys.readouterr().err
    assert "registry check failed: 1 problem(s)" in err and "[M1] Crawler 'census-dhc' has no mise task" in err
    assert main(["crawl", "census-dhc"], paths=paths) == 2  # crawl and build check first
    assert main(["build"], paths=paths) == 2


def test_task_command():
    assert task_command("census-dhc") == "python -m data_pipeline.database crawl census-dhc"
