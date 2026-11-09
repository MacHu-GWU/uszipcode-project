# -*- coding: utf-8 -*-

"""
The only module that talks to the network. It downloads a crawler's declared
files once and keeps them in ``.cache/crawlers/<crawler>/``.

Politeness rules, enforced here for every crawler:

- a cached file is reused: no request, and the secret is not even read;
- downloads run one at a time, ``REQUEST_INTERVAL_S`` apart, with a User-Agent
  that names the project;
- retries only on connection errors, timeouts, 429 and 5xx, with growing waits
  (``Retry-After`` is honoured); any other 4xx fails at once;
- when a connection drops in the middle of a file, the next request asks only for
  the rest (HTTP ``Range``, with ``If-Range`` so that a file changed meanwhile is
  sent whole again); an attempt that brought new bytes is not counted as a failure;
- the body must start with ``Download.magic``, so an HTML error page is never cached;
- ``--refresh`` downloads again at most once per ``REFRESH_COOLDOWN_H`` hours
  (``--force`` overrides); there is no loop, schedule or watch mode.

Secrets are added to the in-memory request only. Messages and the manifest show
the public ``Download.url``; errors are raised ``from None``.
"""

import datetime
import hashlib
import http.client
import json
import os
import time
import typing
import urllib.error
import urllib.parse
import urllib.request

from .core import Crawler, Download, DownloadError, Secret

USER_AGENT = "uszipcode-data-pipeline (+https://github.com/MacHu-GWU/uszipcode-project)"
REQUEST_INTERVAL_S = 2
TIMEOUT_S = 300
ATTEMPTS = 5  # failed attempts in a row that bring no new bytes
MAX_REQUESTS = 30  # requests per file in all, resumed ones included
BACKOFF_S = (5, 15, 45, 90)  # waits after failures 1..4
RETRY_AFTER_MAX_S = 300
REFRESH_COOLDOWN_H = 24
CHUNK = 1 << 20
MANIFEST = "manifest.json"
TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# module attributes so that tests can replace them
urlopen = urllib.request.urlopen
sleep = time.sleep


def utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def read_secret(secret: Secret, crawler_name: str) -> str:
    """The secret from ``$<env>``, else from the file in the home folder."""
    value = os.environ.get(secret.env, "").strip()
    if value:
        return value
    path = os.path.expanduser(secret.file)
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            value = fh.read().strip()
        if value:
            return value
    raise DownloadError("%s needs %s: set the environment variable or save the key in %s (free key: %s)"
                        % (crawler_name, secret.env, secret.file, secret.signup_url))


def crawler_cache_dir(crawler: Crawler, cache_dir: str) -> str:
    return os.path.join(cache_dir, crawler.name)


def load_manifest(folder: str) -> dict:
    path = os.path.join(folder, MANIFEST)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _save_manifest(folder: str, manifest: dict) -> None:
    path = os.path.join(folder, MANIFEST)
    with open(path + ".part", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(path + ".part", path)


def _parse_time(text: str) -> datetime.datetime:
    return datetime.datetime.strptime(text, TIME_FORMAT).replace(tzinfo=datetime.timezone.utc)


def _redact(text: str, secret: typing.Optional[str]) -> str:
    """Hide the secret, also in the URL-encoded form it has inside a request URL."""
    if not secret:
        return text
    for form in (urllib.parse.quote_plus(secret), urllib.parse.quote(secret, safe=""), secret):
        text = text.replace(form, "***")
    return text


def _retry_wait(attempt: int, retry_after: typing.Optional[str]) -> float:
    if retry_after and retry_after.strip().isdigit():
        return min(int(retry_after.strip()), RETRY_AFTER_MAX_S)
    return BACKOFF_S[min(attempt, len(BACKOFF_S)) - 1]


def _remove(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)


def _continues(response, offset: int) -> bool:
    """True if ``response`` is the rest of the file from byte ``offset`` (206 with a matching Content-Range)."""
    content_range = (response.headers.get("Content-Range") or "").replace(" ", "")
    return getattr(response, "status", None) == 206 and content_range.startswith("bytes%d-" % offset)


class _Part:
    """The ``.part`` file of one download: what has arrived so far, with its hash."""

    def __init__(self, path: str):
        self.path = path
        self.restart()

    def restart(self) -> None:
        _remove(self.path)
        self.digest, self.size, self.head = hashlib.sha256(), 0, b""

    def receive(self, response) -> None:
        with open(self.path, "ab") as fh:
            fh.truncate(self.size)  # drop the end of a chunk whose write failed
            while True:
                chunk = response.read(CHUNK)
                if not chunk:
                    return
                if len(self.head) < 16:
                    self.head += chunk[:16 - len(self.head)]
                fh.write(chunk)
                self.digest.update(chunk)
                self.size += len(chunk)


def _download(crawler_name: str, d: Download, path: str) -> typing.Tuple[dict, int]:
    """Download one file to ``path``; returns (manifest entry, number of requests made)."""
    secret = read_secret(d.secret, crawler_name) if d.secret else None
    url, headers = d.url, {"User-Agent": USER_AGENT}
    if d.secret and d.secret.query_param:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode({d.secret.query_param: secret})
    elif d.secret:
        headers["Authorization"] = "Bearer " + secret
    where = "%s: %s" % (crawler_name, d.filename)
    part = _Part(path + ".part")
    validator = last_modified = etag = None  # validator: what If-Range sends when resuming
    requests = failures = most = 0
    last_error = ""
    while True:
        requests += 1
        retry_after = None
        ask = dict(headers)
        if part.size and validator:
            ask.update({"Range": "bytes=%d-" % part.size, "If-Range": validator})
        elif part.size:
            part.restart()
        try:
            with urlopen(urllib.request.Request(url, headers=ask), timeout=TIMEOUT_S) as response:
                if part.size and not _continues(response, part.size):
                    part.restart()  # the whole file again: ranges not supported, or it changed
                last_modified = response.headers.get("Last-Modified") or last_modified
                etag = response.headers.get("ETag") or etag
                validator = validator or etag or last_modified
                part.receive(response)
            if part.size == 0 or not part.head.startswith(d.magic):
                head = part.head[:max(len(d.magic), 4)]
                part.restart()
                hint = " (check %s or %s)" % (d.secret.env, d.secret.file) if d.secret else ""
                raise DownloadError("%s: response starts with %r, expected %r; not cached%s"
                                    % (where, head, d.magic, hint))
            try:
                os.replace(part.path, path)
            except PermissionError:
                raise DownloadError("%s: cannot replace %s: close programs that have it open and run again"
                                    % (where, path)) from None
            entry = {"url": d.url, "bytes": part.size, "sha256": part.digest.hexdigest(),
                     "fetched_at_utc": utcnow().strftime(TIME_FORMAT),
                     "last_modified": last_modified, "etag": etag}
            return entry, requests
        except urllib.error.HTTPError as e:
            if e.code == 416 and part.size:  # the range no longer fits the file: start over
                part.restart()
                validator = None
            elif not (e.code == 429 or 500 <= e.code < 600):
                part.restart()
                raise DownloadError("%s: HTTP %d from %s" % (where, e.code, d.url)) from None
            last_error = "HTTP %d" % e.code
            retry_after = e.headers.get("Retry-After") if e.headers else None
        except (urllib.error.URLError, http.client.HTTPException, OSError) as e:  # resets, timeouts, DNS
            last_error = _redact("%s: %s" % (type(e).__name__, e), secret)
        if part.size > most:  # new bytes arrived: not a failed attempt; resume after the first wait
            most, failures, wait = part.size, 0, BACKOFF_S[0]
        else:
            failures += 1
            wait = _retry_wait(failures, retry_after)
        if failures >= ATTEMPTS or requests >= MAX_REQUESTS:
            part.restart()
            raise DownloadError("%s: gave up after %d attempts (last error: %s) from %s"
                                % (where, requests, last_error, d.url)) from None
        sleep(wait)


def fetch_all(crawler: Crawler, cache_dir: str, refresh: bool = False,
              force: bool = False) -> typing.Tuple[typing.Dict[str, str], int]:
    """
    Make sure every declared download of ``crawler`` is in the cache.
    Returns ``({filename: local path}, number of HTTP requests made)``.
    """
    folder = crawler_cache_dir(crawler, cache_dir)
    os.makedirs(folder, exist_ok=True)
    manifest = load_manifest(folder)
    if refresh and not force:
        times = [_parse_time(manifest[d.filename]["fetched_at_utc"]) for d in crawler.downloads
                 if d.filename in manifest and manifest[d.filename].get("fetched_at_utc")]
        if times:
            newest = max(times)
            age_h = (utcnow() - newest).total_seconds() / 3600
            if age_h < REFRESH_COOLDOWN_H:
                raise DownloadError("%s: last downloaded %s (%.1f h ago); --refresh is allowed once per %d h; add --force to download anyway"
                                    % (crawler.name, newest.strftime(TIME_FORMAT), age_h, REFRESH_COOLDOWN_H))
    files, requests = {}, 0
    for d in crawler.downloads:
        path = os.path.join(folder, d.filename)
        entry = manifest.get(d.filename)
        cached = (not refresh and entry is not None and entry.get("url") == d.url
                  and os.path.isfile(path) and os.path.getsize(path) > 0
                  and entry.get("bytes") == os.path.getsize(path))
        if not cached:
            if requests:
                sleep(REQUEST_INTERVAL_S)
            entry, n = _download(crawler.name, d, path)
            requests += n
            manifest[d.filename] = entry
            _save_manifest(folder, manifest)
        files[d.filename] = path
    return files, requests


def manifest_entries(crawler: Crawler, cache_dir: str) -> typing.Dict[str, dict]:
    """The manifest entries of the crawler's declared downloads (for its output metadata)."""
    manifest = load_manifest(crawler_cache_dir(crawler, cache_dir))
    return {d.filename: manifest[d.filename] for d in crawler.downloads if d.filename in manifest}
