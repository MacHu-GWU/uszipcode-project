# -*- coding: utf-8 -*-

"""
The shape of the code, so that it stays the same as more Fields and crawlers are added:

- ``uszipcode/data/`` and the rest of ``uszipcode`` do not import each other;
- the functionality (the modules of ``uszipcode/data/``) knows no crawler and no Field;
- a crawler only downloads and parses: no network code; it claims Fields by module but never reads a value;
- a Field module imports only ``core``, is named after its Field and carries examples that pass;
- every module is listed in its package's ``MODULES``.
"""

import ast
import os
import types

import pytest

from uszipcode.data import crawlers, fields
from uszipcode.data.checks import unlisted_modules, validate
from uszipcode.data.core import Crawler, Download, Field, column, parse_int
from uszipcode.data.crawl import check_rows
from uszipcode.data.fields import history

DATABASE = "uszipcode.data"
DATABASE_DIR = os.path.dirname(os.path.dirname(crawlers.__file__))
LIBRARY = "uszipcode"
LIBRARY_DIR = os.path.dirname(DATABASE_DIR)
NETWORK = {"urllib", "http", "socket", "ssl", "requests", "ftplib"}


def _imports(path, package):
    """Every dotted name imported by the module at ``path``, with relative imports resolved."""
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                yield a.name
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = package.split(".")
                base = ".".join(parts[:len(parts) - node.level + 1] + ([base] if base else []))
            yield base
            for a in node.names:
                yield base + "." + a.name


def _modules(folder, skip=("__init__.py",)):
    names = sorted(n for n in os.listdir(folder) if n.endswith(".py") and n not in skip)
    assert names
    return [(n, os.path.join(folder, n)) for n in names]


def _inside(name, package):
    return name == package or name.startswith(package + ".")


def _pipeline_modules():
    """(path from uszipcode/, path, package) of every module of uszipcode/data/."""
    found = []
    for folder, _, names in sorted(os.walk(DATABASE_DIR)):
        relative = os.path.relpath(folder, LIBRARY_DIR).replace(os.sep, "/")
        found += [(relative + "/" + n, os.path.join(folder, n), LIBRARY + "." + relative.replace("/", "."))
                  for n in sorted(names) if n.endswith(".py")]
    assert found
    return found


PIPELINE_MODULES = _pipeline_modules()


@pytest.mark.parametrize("name, path, package", PIPELINE_MODULES, ids=[m[0] for m in PIPELINE_MODULES])
def test_the_pipeline_imports_nothing_from_the_library(name, path, package):
    for imported in _imports(path, package):
        assert not _inside(imported, LIBRARY) or _inside(imported, DATABASE), (name, imported)


@pytest.mark.parametrize("name, path", _modules(LIBRARY_DIR, skip=()))
def test_the_library_imports_nothing_from_the_pipeline(name, path):
    for imported in _imports(path, LIBRARY):
        assert not _inside(imported, DATABASE), (name, imported)


@pytest.mark.parametrize("name, path", _modules(DATABASE_DIR, skip=("__init__.py", "__main__.py")))
def test_the_functionality_knows_no_crawler_and_no_field(name, path):
    for imported in _imports(path, DATABASE):
        assert not _inside(imported, DATABASE + ".crawlers"), (name, imported)
        assert not _inside(imported, DATABASE + ".fields"), (name, imported)
        assert not _inside(imported, DATABASE + ".zipcode_universe"), (name, imported)


@pytest.mark.parametrize("name, path", _modules(os.path.dirname(crawlers.__file__)))
def test_a_crawler_only_downloads_and_parses(name, path):
    allowed_packages = (DATABASE + ".core", DATABASE + ".fields", DATABASE + ".keys", DATABASE + ".zipcodes")
    for imported in _imports(path, DATABASE + ".crawlers"):
        assert imported.split(".")[0] not in NETWORK, (name, imported)
        if _inside(imported, LIBRARY):
            assert imported == DATABASE or any(_inside(imported, p) for p in allowed_packages), (name, imported)


def test_a_crawler_never_reads_a_value_itself():
    for name, path in _modules(os.path.dirname(crawlers.__file__)):
        with open(path, encoding="utf-8") as fh:
            assert ".extract" not in fh.read(), name


FIELD_MODULE_FILES = ([(n, p, DATABASE + ".fields") for n, p in _modules(os.path.dirname(fields.__file__))]
                      + [("history/" + n, p, DATABASE + ".fields.history")
                         for n, p in _modules(os.path.dirname(history.__file__))])


@pytest.mark.parametrize("name, path, package", FIELD_MODULE_FILES, ids=[f[0] for f in FIELD_MODULE_FILES])
def test_a_field_module_imports_only_core(name, path, package):
    for imported in _imports(path, package):
        assert imported.split(".")[0] not in NETWORK, (name, imported)
        if _inside(imported, LIBRARY):
            assert imported == DATABASE + ".core" or imported.startswith(DATABASE + ".core."), (name, imported)


@pytest.mark.parametrize("module", fields.MODULES + history.MODULES, ids=lambda m: m.__name__.split(".", 3)[-1])
def test_a_field_module_is_named_after_its_field(module):
    short = module.__name__.rsplit(".", 1)[-1]
    assert isinstance(module.FIELDS, tuple) and module.FIELDS
    for field in module.FIELDS:
        assert field.name == short or field.name.startswith(short + "_")


@pytest.mark.parametrize("field", fields.FIELDS + history.HISTORY_FIELDS, ids=lambda f: f.name)
def test_the_examples_of_every_field_pass(field):
    assert field.examples, "add at least one example of the source row"
    for source_row, expected in field.examples:
        value = field.extract(source_row)
        assert value == expected
        assert value is None or type(value) is field.dtype


def test_every_real_module_is_listed():
    assert unlisted_modules(fields) == [] and unlisted_modules(history) == [] and unlisted_modules(crawlers) == []


def test_an_unlisted_module_is_reported(tmp_path):
    (tmp_path / "listed.py").write_text("", encoding="utf-8")
    (tmp_path / "forgotten.py").write_text("", encoding="utf-8")
    package = types.ModuleType("uszipcode.data.fields")
    package.__path__ = [str(tmp_path)]
    package.MODULES = (types.ModuleType("uszipcode.data.fields.listed"),)
    assert unlisted_modules(package) == ["[L1] fields/forgotten.py is not listed in MODULES in fields/__init__.py: add it."]


def test_a_module_can_generate_a_group_of_fields(tmp_path):
    """A distribution: one module, one column per number, generated by a loop."""
    bands = ("under_18", "18_to_64", "65_and_over")
    group = tuple(
        Field("population_by_age_" + band, int, "Population of the ZCTA aged %s" % band, "people",
              extract=column("AGE_%d" % i, parse_int))
        for i, band in enumerate(bands)
    )
    crawler = Crawler("acs-demo", tuple(f.name for f in group), (Download("a.json", "https://data.test/a.json"),),
                      lambda files: [])
    assert validate(list(group), [crawler], None) == []
    records, stats = check_rows(crawler, {f.name: f for f in group},
                                [("20037", {"AGE_0": "10", "AGE_1": "20", "AGE_2": ""}),
                                 ("10001", {"AGE_0": "1", "AGE_1": "2", "AGE_2": "3"})])
    assert records == [("10001", [1, 2, 3]), ("20037", [10, 20, None])]
    assert stats["non_null"]["population_by_age_65_and_over"] == 1
