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
ATTEMPTS = 5
BACKOFF_S = (5, 15, 45, 90)  # waits after attempts 1..4
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


def _download(crawler_name: str, d: Download, path: str) -> typing.Tuple[dict, int]:
    """Download one file to ``path``; returns (manifest entry, number of requests made)."""
    secret = read_secret(d.secret, crawler_name) if d.secret else None
    url, headers = d.url, {"User-Agent": USER_AGENT}
    if d.secret and d.secret.query_param:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode({d.secret.query_param: secret})
    elif d.secret:
        headers["Authorization"] = "Bearer " + secret
    where = "%s: %s" % (crawler_name, d.filename)
    part = path + ".part"
    last_error = ""
    for attempt in range(1, ATTEMPTS + 1):
        retry_after = None
        try:
            request = urllib.request.Request(url, headers=headers)
            with urlopen(request, timeout=TIMEOUT_S) as response:
                digest, size, head = hashlib.sha256(), 0, b""
                with open(part, "wb") as fh:
                    while True:
                        chunk = response.read(CHUNK)
                        if not chunk:
                            break
                        if len(head) < 16:
                            head += chunk[:16 - len(head)]
                        digest.update(chunk)
                        size += len(chunk)
                        fh.write(chunk)
                last_modified = response.headers.get("Last-Modified")
                etag = response.headers.get("ETag")
            if size == 0 or not head.startswith(d.magic):
                _remove(part)
                hint = " (check %s or %s)" % (d.secret.env, d.secret.file) if d.secret else ""
                raise DownloadError("%s: response starts with %r, expected %r; not cached%s"
                                    % (where, head[:max(len(d.magic), 4)], d.magic, hint))
            try:
                os.replace(part, path)
            except PermissionError:
                raise DownloadError("%s: cannot replace %s: close programs that have it open and run again"
                                    % (where, path)) from None
            entry = {"url": d.url, "bytes": size, "sha256": digest.hexdigest(),
                     "fetched_at_utc": utcnow().strftime(TIME_FORMAT),
                     "last_modified": last_modified, "etag": etag}
            return entry, attempt
        except urllib.error.HTTPError as e:
            _remove(part)
            if not (e.code == 429 or 500 <= e.code < 600):
                raise DownloadError("%s: HTTP %d from %s" % (where, e.code, d.url)) from None
            last_error = "HTTP %d" % e.code
            retry_after = e.headers.get("Retry-After") if e.headers else None
        except (urllib.error.URLError, http.client.HTTPException, OSError) as e:  # resets, timeouts, DNS
            _remove(part)
            last_error = _redact("%s: %s" % (type(e).__name__, e), secret)
        if attempt < ATTEMPTS:
            sleep(_retry_wait(attempt, retry_after))
    raise DownloadError("%s: gave up after %d attempts (last error: %s) from %s"
                        % (where, ATTEMPTS, last_error, d.url)) from None


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
