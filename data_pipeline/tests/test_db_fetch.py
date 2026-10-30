# -*- coding: utf-8 -*-

"""
fetch.py: the cache, the refresh guard, retries, pacing and secrets. Uses FakeOpener only.
"""

import datetime
import hashlib
import json
import os

import pytest

from data_pipeline.database import fetch
from data_pipeline.database.core import Crawler, Download, DownloadError, Secret

from fakes import FakeOpener

URL = "https://data.test/a.csv"
BODY = b"zipcode,a\n10001,1\n"
KEY = "SECRET-TEST-123"
T0 = datetime.datetime(2026, 10, 30, 8, 0, 0, tzinfo=datetime.timezone.utc)


def _crawler(*downloads, name="src"):
    return Crawler(name, ("a",), downloads or (Download("a.csv", URL, magic=b"zipcode,"),), lambda files: [])


def _secret(**kw):
    kw.setdefault("query_param", "key")
    return Secret("FAKE_KEY", "~/.fake_key", "https://signup.test/", **kw)


@pytest.fixture
def cache(tmp_path):
    return str(tmp_path / "cache")


@pytest.fixture
def opener(monkeypatch):
    o = FakeOpener({URL: BODY})
    monkeypatch.setattr(fetch, "urlopen", o)
    return o


@pytest.fixture
def clock(monkeypatch):
    now = [T0]
    monkeypatch.setattr(fetch, "utcnow", lambda: now[0])
    return now


def _manifest(cache, name="src"):
    with open(os.path.join(cache, name, "manifest.json"), encoding="utf-8") as fh:
        return json.load(fh)


def test_miss_writes_file_and_manifest(cache, opener, clock):
    files, requests = fetch.fetch_all(_crawler(), cache)
    assert requests == 1 and files == {"a.csv": os.path.join(cache, "src", "a.csv")}
    with open(files["a.csv"], "rb") as fh:
        assert fh.read() == BODY
    assert _manifest(cache)["a.csv"] == {
        "url": URL, "bytes": len(BODY), "sha256": hashlib.sha256(BODY).hexdigest(),
        "fetched_at_utc": "2026-10-30T08:00:00Z", "last_modified": "Thu, 01 Oct 2026 00:00:00 GMT", "etag": '"fake"'}
    url, headers, timeout = opener.calls[0]
    assert url == URL and headers["User-agent"] == fetch.USER_AGENT and timeout == fetch.TIMEOUT_S
    assert not [n for n in os.listdir(os.path.join(cache, "src")) if n.endswith(".part")]


def test_hit_makes_no_request_and_reads_no_secret(cache, opener, monkeypatch):
    crawler = _crawler(Download("a.csv", URL, magic=b"zipcode,", secret=_secret()))
    monkeypatch.setenv("FAKE_KEY", KEY)
    assert fetch.fetch_all(crawler, cache)[1] == 1
    monkeypatch.delenv("FAKE_KEY")  # a cache hit must not need the key
    assert fetch.fetch_all(crawler, cache)[1] == 0
    assert len(opener.calls) == 1


def test_changed_url_or_damaged_file_downloads_again(cache, opener):
    fetch.fetch_all(_crawler(), cache)
    other = "https://data.test/v2/a.csv"
    opener.served[other] = BODY
    assert fetch.fetch_all(_crawler(Download("a.csv", other, magic=b"zipcode,")), cache)[1] == 1
    with open(os.path.join(cache, "src", "a.csv"), "ab") as fh:
        fh.write(b"extra")  # size no longer matches the manifest
    assert fetch.fetch_all(_crawler(Download("a.csv", other, magic=b"zipcode,")), cache)[1] == 1
    assert opener.urls == [URL, other, other]


def test_refresh_guard(cache, opener, clock):
    fetch.fetch_all(_crawler(), cache)
    clock[0] = T0 + datetime.timedelta(hours=3.2)
    with pytest.raises(DownloadError) as e:
        fetch.fetch_all(_crawler(), cache, refresh=True)
    assert str(e.value) == ("src: last downloaded 2026-10-30T08:00:00Z (3.2 h ago); --refresh is allowed once "
                            "per 24 h; add --force to download anyway")
    assert fetch.fetch_all(_crawler(), cache, refresh=True, force=True)[1] == 1
    clock[0] = T0 + datetime.timedelta(hours=3.2 + 25)
    assert fetch.fetch_all(_crawler(), cache, refresh=True)[1] == 1
    assert len(opener.calls) == 3


def test_retries_on_503_with_backoff(cache, opener, sleeps):
    opener.script[URL] = [("http", 503), ("http", 503)]
    assert fetch.fetch_all(_crawler(), cache)[1] == 3
    assert sleeps == [5, 15]


def test_retry_after_is_honoured_and_capped(cache, opener, sleeps):
    opener.script[URL] = [("http", 503, "30"), ("http", 429, "1000")]
    assert fetch.fetch_all(_crawler(), cache)[1] == 3
    assert sleeps == [30, fetch.RETRY_AFTER_MAX_S]


def test_gives_up_after_5_attempts(cache, opener, sleeps):
    opener.script[URL] = [("http", 503)] * 5
    with pytest.raises(DownloadError) as e:
        fetch.fetch_all(_crawler(), cache)
    assert str(e.value) == "src: a.csv: gave up after 5 attempts (last error: HTTP 503) from %s" % URL
    assert e.value.__cause__ is None and e.value.__suppress_context__
    assert sleeps == [5, 15, 45, 90] and len(opener.calls) == 5
    assert not os.path.exists(os.path.join(cache, "src", "a.csv"))


def test_404_fails_at_once(cache, opener, sleeps):
    opener.script[URL] = [("http", 404)]
    with pytest.raises(DownloadError) as e:
        fetch.fetch_all(_crawler(), cache)
    assert str(e.value) == "src: a.csv: HTTP 404 from %s" % URL
    assert len(opener.calls) == 1 and sleeps == []


def test_magic_mismatch_is_not_cached_and_keeps_the_old_file(cache, opener):
    fetch.fetch_all(_crawler(), cache)
    before = _manifest(cache)
    opener.served[URL] = b"<html><body>Service unavailable</body></html>"
    with pytest.raises(DownloadError) as e:
        fetch.fetch_all(_crawler(), cache, refresh=True, force=True)
    assert "src: a.csv: response starts with b'<html><b', expected b'zipcode,'; not cached" in str(e.value)
    with open(os.path.join(cache, "src", "a.csv"), "rb") as fh:
        assert fh.read() == BODY
    assert _manifest(cache) == before
    assert sorted(os.listdir(os.path.join(cache, "src"))) == ["a.csv", "manifest.json"]


def test_magic_mismatch_hints_at_the_secret(cache, monkeypatch):
    monkeypatch.setattr(fetch, "urlopen", FakeOpener({URL: b"<html>invalid key</html>"}))
    monkeypatch.setenv("FAKE_KEY", KEY)
    with pytest.raises(DownloadError) as e:
        fetch.fetch_all(_crawler(Download("a.csv", URL, magic=b"[[", secret=_secret())), cache)
    assert str(e.value) == "src: a.csv: response starts with b'<htm', expected b'[['; not cached (check FAKE_KEY or ~/.fake_key)"


def test_mid_body_reset_restarts_from_byte_0(cache, opener, sleeps):
    opener.script[URL] = ["reset"]
    files, requests = fetch.fetch_all(_crawler(), cache)
    assert requests == 2 and sleeps == [5]
    with open(files["a.csv"], "rb") as fh:
        assert fh.read() == BODY
    assert _manifest(cache)["a.csv"]["bytes"] == len(BODY)


def test_downloads_are_paced(cache, opener, sleeps):
    downloads = [Download("p%d.csv" % i, "https://data.test/p%d.csv" % i, magic=b"zipcode,") for i in range(3)]
    for d in downloads:
        opener.served[d.url] = BODY
    files, requests = fetch.fetch_all(_crawler(*downloads), cache)
    assert requests == 3 and sleeps == [fetch.REQUEST_INTERVAL_S] * 2
    assert opener.urls == [d.url for d in downloads]  # declared order, one at a time
    assert list(files) == ["p0.csv", "p1.csv", "p2.csv"]


def test_secret_from_env_and_from_home_file(cache, opener, monkeypatch, home):
    crawler = _crawler(Download("a.csv", URL + "?get=x", magic=b"zipcode,", secret=_secret()))
    monkeypatch.setenv("FAKE_KEY", KEY)
    fetch.fetch_all(crawler, cache)
    assert opener.urls[-1] == URL + "?get=x&key=" + KEY
    monkeypatch.delenv("FAKE_KEY")
    (home / ".fake_key").write_text("  file-key-456\n", encoding="utf-8")
    fetch.fetch_all(crawler, cache, refresh=True, force=True)
    assert opener.urls[-1] == URL + "?get=x&key=file-key-456"
    assert _manifest(cache)["a.csv"]["url"] == URL + "?get=x"  # the public URL only


def test_missing_secret_makes_no_request(cache, opener):
    with pytest.raises(DownloadError) as e:
        fetch.fetch_all(_crawler(Download("a.csv", URL, magic=b"zipcode,", secret=_secret())), cache)
    assert str(e.value) == ("src needs FAKE_KEY: set the environment variable or save the key in ~/.fake_key "
                            "(free key: https://signup.test/)")
    assert opener.calls == []


def test_bearer_header(cache, opener, monkeypatch):
    monkeypatch.setenv("FAKE_KEY", KEY)
    fetch.fetch_all(_crawler(Download("a.csv", URL, magic=b"zipcode,", secret=_secret(query_param="", bearer=True))), cache)
    url, headers, _ = opener.calls[0]
    assert url == URL and headers["Authorization"] == "Bearer " + KEY


def test_the_secret_is_never_written_or_shown(tmp_path, cache, opener, monkeypatch, capsys):
    monkeypatch.setenv("FAKE_KEY", KEY)
    secret = _secret()
    ok = _crawler(Download("a.csv", URL, magic=b"zipcode,", secret=secret))
    fetch.fetch_all(ok, cache)
    messages = []
    failing = [
        ("missing", [("http", 404)]),
        ("reset", [("urlerror", "cannot reach %(url)s")] * 5),
        ("magic", None),
    ]
    for name, script in failing:
        url = "https://data.test/%s.csv" % name
        opener.served[url] = BODY if script else b"<html>bad key</html>"
        if script:
            opener.script[url] = script
        with pytest.raises(DownloadError) as e:
            fetch.fetch_all(_crawler(Download("x.csv", url, magic=b"zipcode,", secret=secret), name="src-" + name), cache)
        messages.append(str(e.value))
    assert any("cannot reach https://data.test/reset.csv?key=***" in m for m in messages)
    assert fetch._redact("bad url ?key=a%2Bb%2Fc", "a+b/c") == "bad url ?key=***"  # URL-encoded too
    assert all(KEY in u for u in opener.urls)  # the key was sent ...
    assert not any(KEY in m for m in messages)  # ... but never shown
    out, err = capsys.readouterr()
    assert KEY not in out and KEY not in err
    for folder, _, names in os.walk(tmp_path):
        for n in names:
            with open(os.path.join(folder, n), "rb") as fh:
                assert KEY.encode() not in fh.read(), os.path.join(folder, n)
