# -*- coding: utf-8 -*-

"""
Command line of the database step (run from the repository root)::

    python -m data_pipeline.database check
    python -m data_pipeline.database crawl NAME [--refresh] [--force]
    python -m data_pipeline.database crawl --all [--refresh] [--force]
    python -m data_pipeline.database build [--pk-set demo|full|PATH]

The mise tasks in ``mise.toml`` call these commands; ``mise run crawler-<name>``
runs ``crawl <name>``. Exit codes: 0 success, 2 registry / contract / PK-set
problems, 1 download and file problems. Expected errors print no traceback.
"""

import argparse
import difflib
import os
import sys
import typing

from . import build as build_mod
from .core import Paths, PipelineError, RegistryError
from .crawl import run_crawler
from .registry import CRAWLERS, describe, require_valid, validate
from .fields import FIELDS


def _rel(path: str) -> str:
    try:
        return os.path.relpath(path)
    except ValueError:  # another drive on Windows
        return path


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m data_pipeline.database",
                                description="Crawler registry of the uszipcode 3.0 database.")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="check the Field catalog, the claims and the mise tasks; print the catalog")
    c = sub.add_parser("crawl", help="run one crawler (or --all): download once, parse, write its output")
    c.add_argument("name", nargs="?", help="crawler name, e.g. census-dhc")
    c.add_argument("--all", action="store_true", help="run every crawler, one after another")
    c.add_argument("--refresh", action="store_true", help="download the files again (at most once per 24 h)")
    c.add_argument("--force", action="store_true", help="with --refresh: ignore the 24 h guard")
    b = sub.add_parser("build", help="join every crawler output onto a PK set")
    b.add_argument("--pk-set", default="demo", help="demo (default), full, or the path of a CSV with a zipcode column")
    return p


def _crawl_line(s: dict) -> str:
    if s["requests"]:
        how = "downloaded now, %d request(s)" % s["requests"]
    else:
        how = "cached %s, 0 requests; add -- --refresh to download again" % ", ".join(s["fetched"])
    return "%s: %d file(s) (%s), %d rows, %d skipped keys -> %s" % (
        s["crawler"], s["files"], how, s["rows"], s["skipped_keys"], _rel(s["path"]))


def main(argv: typing.Optional[typing.List[str]] = None, fields=None, crawlers=None,
         paths: typing.Optional[Paths] = None) -> int:
    fields = FIELDS if fields is None else fields
    crawlers = CRAWLERS if crawlers is None else crawlers
    paths = Paths.default() if paths is None else paths
    args = _parser().parse_args(argv)
    try:
        if args.command == "check":
            problems = validate(fields, crawlers, paths.mise_toml)
            if problems:
                raise RegistryError(problems)
            print("%d Fields, %d crawlers, every Field claimed once, mise tasks match." % (len(fields), len(crawlers)))
            print(describe(fields, crawlers))
            return 0
        if args.command == "crawl":
            if bool(args.name) == bool(args.all):
                print("crawl needs exactly one of NAME or --all", file=sys.stderr)
                return 2
            require_valid(fields, crawlers, paths.mise_toml)
            if args.all:
                selected = list(crawlers)
            else:
                by_name = {c.name: c for c in crawlers}
                if args.name not in by_name:
                    close = difflib.get_close_matches(args.name, list(by_name), n=1)
                    hint = " (did you mean %r?)" % close[0] if close else ""
                    print("unknown crawler %r%s; known: %s" % (args.name, hint, ", ".join(sorted(by_name))), file=sys.stderr)
                    return 2
                selected = [by_name[args.name]]
            if args.force and not args.refresh:
                print("--force only has an effect together with --refresh", file=sys.stderr)
            for crawler in selected:
                summary = run_crawler(crawler, fields, paths, refresh=args.refresh, force=args.force)
                print(_crawl_line(summary), flush=True)
            return 0
        if args.command == "build":
            coverage = build_mod.build(fields, crawlers, paths, pk_set=args.pk_set)
            print(build_mod.describe_coverage(coverage))
            print("wrote %s, %s and %s" % (_rel(coverage["files"]["sqlite"]), _rel(coverage["files"]["csv"]),
                                           _rel(coverage["files"]["sqlite"][:-len(".sqlite")] + "_coverage.json")))
            return 0
    except PipelineError as e:
        print(str(e), file=sys.stderr)
        return e.exit_code
    return 2  # pragma: no cover
