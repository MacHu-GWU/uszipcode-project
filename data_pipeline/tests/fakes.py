# -*- coding: utf-8 -*-

"""
Test doubles for the database step.

- :class:`FakeOpener` replaces ``fetch.urlopen``: it serves bytes per URL, records
  every request and can fail on purpose (HTTP errors, connection resets).
- :func:`make_fake_world` builds a registry of any size (N PKs, M Fields,
  K crawlers) with the files its crawlers download and the database it must give.
"""

import csv
import email.message
import io
import os
import typing
import urllib.error

from data_pipeline.database.core import Crawler, Download, Field, Paths
from data_pipeline.database.registry import task_command


class _Response:
    def __init__(self, body: bytes, reset: bool = False):
        self._body, self._pos, self._reset = body, 0, reset
        self.headers = {"Last-Modified": "Thu, 01 Oct 2026 00:00:00 GMT", "ETag": '"fake"'}

    def read(self, n: int = -1) -> bytes:
        if self._reset and self._pos > 0:
            raise ConnectionResetError("connection reset by peer")
        if self._reset:  # half the body, then the connection drops
            n = max(1, len(self._body) // 2)
        chunk = self._body[self._pos:] if n < 0 else self._body[self._pos:self._pos + n]
        self._pos += len(chunk)
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def http_error(url: str, code: int, retry_after: typing.Optional[str] = None) -> urllib.error.HTTPError:
    headers = email.message.Message()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return urllib.error.HTTPError(url, code, "fake %d" % code, headers, io.BytesIO(b""))


class FakeOpener:
    """
    ``served``: public URL -> body. A request matches the longest served URL it starts
    with, so a secret appended as ``&key=...`` still matches. ``script``: public URL ->
    list of actions used by the next requests, one per request:
    ``("http", code)``, ``("http", code, retry_after)``, ``"reset"`` (half the body,
    then ``ConnectionResetError``), ``("urlerror", text)`` or ``"ok"``.
    """

    def __init__(self, served: typing.Dict[str, bytes], script: typing.Optional[typing.Dict[str, list]] = None):
        self.served = served
        self.script = {url: list(actions) for url, actions in (script or {}).items()}
        self.calls = []  # (full url, {header: value}, timeout)

    def _match(self, url: str) -> typing.Optional[str]:
        matches = [u for u in self.served if url.startswith(u)]
        return max(matches, key=len) if matches else None

    def __call__(self, request, timeout=None):
        url = request.full_url
        self.calls.append((url, dict(request.header_items()), timeout))
        public = self._match(url)
        if public is None:
            raise http_error(url, 404)
        actions = self.script.get(public)
        action = actions.pop(0) if actions else "ok"
        if action == "reset":
            return _Response(self.served[public], reset=True)
        if isinstance(action, tuple) and action[0] == "http":
            raise http_error(url, *action[1:])
        if isinstance(action, tuple) and action[0] == "urlerror":
            raise urllib.error.URLError(action[1] % {"url": url})
        return _Response(self.served[public])

    @property
    def urls(self) -> typing.List[str]:
        return [c[0] for c in self.calls]


# ------------------------------------------------------------------------------------- fake world
DTYPES = (int, float, str)
OUTSIDE = ("99001", "99002")  # in every source, not in the PK set
SKIPPED = "00000"  # in every source, not a ZIP


def _value(dtype: type, k: int, i: int, bump: int):
    if dtype is int:
        return 100 * k + i + 7 * bump
    if dtype is float:
        return k + i / 8 + bump
    return "v%d_%d%s" % (k, i, "b" * bump)


def _parser(filename: str, fields: typing.List[Field]):
    def parse(files):
        with open(files[filename], encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                yield row["zipcode"], {f.name: None if row[f.name] == "" else f.dtype(row[f.name]) for f in fields}
    return parse


class FakeWorld:
    """
    PK k is ``"%05d" % (501 + 37 * k)``. Field i (0-based, named ``f%02d % (i + 1)``)
    has dtype ``DTYPES[i % 3]`` and belongs to crawler j = i % K (named ``fake-<j+1>``).
    Source j leaves out PK k when k == N - 1 (a "PO box" in no source) or
    (k + j) % 3 == 0, and leaves the cell (k, i) blank when (k + i) % 4 == 0.
    """

    def __init__(self, root: str, n_pks: int, n_fields: int, n_crawlers: int):
        assert n_fields >= n_crawlers >= 1 and n_pks >= 1
        self.root, self.n, self.m, self.k = root, n_pks, n_fields, n_crawlers
        self.pks = ["%05d" % (501 + 37 * k) for k in range(n_pks)]
        self.fields = [Field("f%02d" % (i + 1), DTYPES[i % 3], "fake field %d" % (i + 1)) for i in range(n_fields)]
        self.crawlers, self.served = [], {}
        for j in range(n_crawlers):
            claimed = [f for i, f in enumerate(self.fields) if i % n_crawlers == j]
            filename = "fake-%d.csv" % (j + 1)
            download = Download(filename, "https://fake.test/" + filename, magic=b"zipcode,")
            self.crawlers.append(Crawler("fake-%d" % (j + 1), tuple(f.name for f in claimed), (download,),
                                         _parser(filename, claimed)))
            self.served[download.url] = self.source_bytes(j)
        self.paths = Paths.under(root)
        os.makedirs(root, exist_ok=True)
        with open(self.paths.mise_toml, "w", encoding="utf-8", newline="\n") as fh:
            for c in self.crawlers:
                fh.write('[tasks.crawler-%s]\nrun = "%s"\n\n' % (c.name, task_command(c.name)))
        self.pk_csv = os.path.join(root, "pks_fake.csv")
        with open(self.pk_csv, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("zipcode\n" + "".join(pk + "\n" for pk in reversed(self.pks)))

    def owner_index(self, i: int) -> int:
        return i % self.k

    def in_source(self, k: int, j: int) -> bool:
        return not (k == self.n - 1 or (k + j) % 3 == 0)

    def source_bytes(self, j: int, bump: int = 0) -> bytes:
        """The file crawler j serves; ``bump`` changes every value."""
        idx = [i for i in range(self.m) if i % self.k == j]
        rows = []
        for k, pk in enumerate(self.pks):
            if self.in_source(k, j):
                rows.append([pk] + ["" if (k + i) % 4 == 0 else _value(DTYPES[i % 3], k, i, bump) for i in idx])
        for extra, zipcode in enumerate(OUTSIDE + (SKIPPED,)):
            rows.append([zipcode] + [_value(DTYPES[i % 3], self.n + extra, i, bump) for i in idx])
        rows.sort(key=lambda r: r[0], reverse=True)
        out = io.StringIO()
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(["zipcode"] + [self.fields[i].name for i in idx])
        writer.writerows(rows)
        return out.getvalue().encode("utf-8")

    def expected(self, bumps: typing.Optional[typing.Dict[int, int]] = None) -> typing.List[list]:
        """The database rows: one per PK (sorted), ``[zipcode] + [value or None per Field]``."""
        bumps = bumps or {}
        rows = []
        for k, pk in enumerate(self.pks):
            row = [pk]
            for i in range(self.m):
                j = self.owner_index(i)
                gap = not self.in_source(k, j) or (k + i) % 4 == 0
                row.append(None if gap else _value(DTYPES[i % 3], k, i, bumps.get(j, 0)))
            rows.append(row)
        return sorted(rows)

    def not_in_source(self, i: int) -> int:
        return sum(1 for k in range(self.n) if not self.in_source(k, self.owner_index(i)))


def make_fake_world(root: str, n_pks: int, n_fields: int, n_crawlers: int) -> FakeWorld:
    return FakeWorld(root, n_pks, n_fields, n_crawlers)
