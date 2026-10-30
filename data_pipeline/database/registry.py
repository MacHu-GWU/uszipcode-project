# -*- coding: utf-8 -*-

"""
The registry: the list of crawlers, and the checks that tie it to the Field catalog
and to ``mise.toml``.

``validate()`` collects every problem instead of stopping at the first one. Each
problem is one sentence ``[ID] what is wrong: how to fix it``. Importing a module
validates nothing; ``check``, ``crawl`` and ``build`` call ``require_valid()`` first.

Rules: F1-F5 Fields, C1-C8 crawlers, K1-K3 claims (every Field claimed exactly
once), M0-M2 mise tasks (every crawler has ``crawler-<name>`` and vice versa).
"""

import collections
import difflib
import os
import re
import typing
import urllib.parse

from .core import Crawler, Field, RegistryError, SQL_TYPES
from .fields import FIELDS
from .crawlers import census_gazetteer, census_dhc

#: every crawler, in the order ``crawl --all`` runs them
CRAWLERS = [census_gazetteer.CRAWLER, census_dhc.CRAWLER]

TASK_PREFIX = "crawler-"
MAX_DOWNLOADS = 100
FIELD_NAME = re.compile(r"^[a-z][a-z0-9_]{0,59}$")
CRAWLER_NAME = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
FILENAME = re.compile(r"^[A-Za-z0-9._-]{1,60}$")
SECRET_PARAMS = {"key", "token", "api_key", "apikey", "access_token"}


def task_command(name: str) -> str:
    """The command a ``crawler-<name>`` mise task must run."""
    return "python -m data_pipeline.database crawl " + name


def task_block(name: str) -> str:
    return '[tasks.%s%s]\nrun = "%s"' % (TASK_PREFIX, name, task_command(name))


def owners(crawlers: typing.Sequence[Crawler]) -> typing.Dict[str, str]:
    """Field name -> name of the crawler that claims it."""
    return {f: c.name for c in crawlers for f in c.fields}


def _did_you_mean(word: str, options: typing.Iterable[str]) -> str:
    close = difflib.get_close_matches(word, list(options), n=1)
    return " (did you mean %r?)" % close[0] if close else ""


def _check_fields(fields: typing.Sequence[Field]) -> typing.List[str]:
    problems, seen = [], set()
    for f in fields:
        if not FIELD_NAME.match(f.name or ""):
            problems.append("[F1] Field name %r is not snake_case (a-z, 0-9, _; starts with a letter): rename it." % f.name)
        if f.name == "zipcode":
            problems.append("[F2] Field name 'zipcode' is reserved for the primary key: rename the Field.")
        if f.name in seen:
            problems.append("[F3] Field %r is defined twice in FIELDS: keep one." % f.name)
        seen.add(f.name)
        if f.dtype not in SQL_TYPES:
            problems.append("[F4] Field %r has dtype %s: use int, float or str." % (f.name, getattr(f.dtype, "__name__", f.dtype)))
        if not (f.description or "").strip():
            problems.append('[F5] Field %r has an empty description: describe it (say "ZCTA" for Census values).' % f.name)
    return problems


def _check_crawlers(crawlers: typing.Sequence[Crawler]) -> typing.List[str]:
    problems = []
    names = collections.Counter(c.name for c in crawlers)
    for name, n in names.items():
        if n > 1:
            problems.append("[C2] Crawler name %r is used %d times: names must be unique." % (name, n))
    url_users = collections.defaultdict(list)
    for c in crawlers:
        if not CRAWLER_NAME.match(c.name or "") or len(c.name) > 30:
            problems.append("[C1] Crawler name %r is not kebab-case (a-z, 0-9, single dashes, at most 30 characters): rename it." % c.name)
        if not c.fields:
            problems.append("[C3] Crawler %r claims no Fields: add at least one." % c.name)
        if not (1 <= len(c.downloads) <= MAX_DOWNLOADS):
            problems.append("[C4] Crawler %r declares %d downloads (allowed 1 to %d): a crawler downloads whole files, never one request per ZIP."
                            % (c.name, len(c.downloads), MAX_DOWNLOADS))
        filenames = collections.Counter(d.filename for d in c.downloads)
        for d in c.downloads:
            if not FILENAME.match(d.filename or ""):
                problems.append("[C5] Crawler %r: download filename %r must be 1-60 characters of A-Z a-z 0-9 . _ -." % (c.name, d.filename))
        for fn, n in filenames.items():
            if n > 1:
                problems.append("[C5] Crawler %r: download filename %r is used %d times: filenames must be unique." % (c.name, fn, n))
        for d in c.downloads:
            parts = urllib.parse.urlsplit(d.url or "")
            if parts.scheme != "https":
                problems.append("[C6] Crawler %r: URL %s must start with https://." % (c.name, d.url))
            params = {k.lower() for k, _ in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)}
            leaked = sorted(params & SECRET_PARAMS)
            if leaked:
                problems.append("[C6] Crawler %r: URL %s has a %s parameter: put the secret in Download.secret, never in the URL."
                                % (c.name, d.url, "/".join(leaked)))
            s = d.secret
            if s is not None:
                if bool(s.query_param) == bool(s.bearer):
                    problems.append("[C7] Crawler %r: the Secret of %r must set exactly one of query_param or bearer." % (c.name, d.filename))
                if not (s.file or "").startswith("~/"):
                    problems.append("[C7] Crawler %r: the Secret file %r must be in the home folder (start with ~/)." % (c.name, s.file))
            url_users[d.url].append(c.name)
    for url, users in url_users.items():
        if len(set(users)) > 1:
            problems.append("[C8] URL %s is downloaded by both %s: one source, one crawler." % (url, " and ".join(repr(u) for u in sorted(set(users)))))
    return problems


def _check_claims(fields: typing.Sequence[Field], crawlers: typing.Sequence[Crawler]) -> typing.List[str]:
    problems = []
    catalog = [f.name for f in fields]
    known = set(catalog)
    claims = collections.defaultdict(list)
    for c in crawlers:
        for name in c.fields:
            if name in known:
                claims[name].append(c.name)
            else:
                problems.append("[K1] Crawler %r claims %r, which is not in FIELDS%s: add the Field to fields.py or fix the name."
                                % (c.name, name, _did_you_mean(name, catalog)))
    for name in dict.fromkeys(catalog):  # catalog order, without duplicates
        claimants = claims.get(name, [])
        if len(claimants) > 1:
            problems.append("[K2] Field %r is claimed %d times (%s): exactly one crawler may claim it."
                            % (name, len(claimants), ", ".join(claimants)))
        elif not claimants:
            problems.append("[K3] Field %r is not claimed by any crawler: add it to one crawler's fields." % name)
    return problems


def _load_toml(path: str):
    try:
        import tomllib  # Python 3.11+
    except ImportError:  # pragma: no cover
        return None, "[M0] mise.toml cannot be checked: Python 3.11 or newer is needed (tomllib)."
    if not os.path.exists(path):
        return None, "[M0] mise.toml not found at %s: create it (see data_pipeline/database/README.md)." % path
    try:
        with open(path, "rb") as fh:
            return tomllib.load(fh), None
    except tomllib.TOMLDecodeError as e:
        return None, "[M0] mise.toml is not valid TOML: %s" % e


def _check_mise(crawlers: typing.Sequence[Crawler], mise_toml: str) -> typing.List[str]:
    data, problem = _load_toml(mise_toml)
    if problem:
        return [problem]
    tasks = data.get("tasks", {}) if isinstance(data, dict) else {}
    problems = []
    names = [c.name for c in crawlers]
    for name in dict.fromkeys(names):
        task = tasks.get(TASK_PREFIX + name)
        if task is None:
            problems.append("[M1] Crawler %r has no mise task: add to mise.toml\n%s" % (name, task_block(name)))
            continue
        run = task if isinstance(task, str) else task.get("run") if isinstance(task, dict) else None
        if run != task_command(name):
            problems.append('[M1] mise task %r runs %r: expected "%s".' % (TASK_PREFIX + name, run, task_command(name)))
    for task_name in tasks:
        if task_name.startswith(TASK_PREFIX) and task_name[len(TASK_PREFIX):] not in names:
            problems.append("[M2] mise task %r has no crawler named %r%s: remove the task or register the crawler."
                            % (task_name, task_name[len(TASK_PREFIX):], _did_you_mean(task_name[len(TASK_PREFIX):], names)))
    return problems


def validate(fields: typing.Sequence[Field], crawlers: typing.Sequence[Crawler],
             mise_toml: typing.Optional[str]) -> typing.List[str]:
    """Every problem of the catalog, the crawlers, the claims and (unless ``mise_toml`` is None) the mise tasks."""
    problems = _check_fields(fields) + _check_crawlers(crawlers) + _check_claims(fields, crawlers)
    if mise_toml is not None:
        problems += _check_mise(crawlers, mise_toml)
    return problems


def require_valid(fields, crawlers, mise_toml) -> None:
    problems = validate(fields, crawlers, mise_toml)
    if problems:
        raise RegistryError(problems)


def describe(fields: typing.Sequence[Field], crawlers: typing.Sequence[Crawler]) -> str:
    """The Field catalog as a table: name, type, unit, claiming crawler."""
    owner = owners(crawlers)
    rows = [("field", "type", "unit", "crawler")]
    rows += [(f.name, f.dtype.__name__, f.unit or "-", owner.get(f.name, "-")) for f in fields]
    widths = [max(len(r[i]) for r in rows) for i in range(4)]
    return "\n".join("  " + "  ".join(cell.ljust(w) for cell, w in zip(r, widths)).rstrip() for r in rows)
