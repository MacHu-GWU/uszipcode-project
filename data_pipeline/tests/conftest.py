# -*- coding: utf-8 -*-

"""
Shared fixtures: no test may reach the network or the real home folder.

- every socket connect raises, and ``fetch.urlopen`` raises until a test installs a FakeOpener;
- ``fetch.sleep`` records the waits instead of sleeping (fixture ``sleeps``);
- the home folder is an empty tmp folder and ``CENSUS_API_KEY`` is unset, so the
  real ``~/.census_key`` is never read.
"""

import socket

import pytest

from data_pipeline.database import fetch


def _no_network(*args, **kwargs):
    raise RuntimeError("network disabled in tests")


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setattr(socket.socket, "connect", _no_network)
    monkeypatch.setattr(socket.socket, "connect_ex", _no_network)
    monkeypatch.setattr(fetch, "urlopen", _no_network)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv("CENSUS_API_KEY", raising=False)


@pytest.fixture(autouse=True)
def sleeps(monkeypatch):
    waits = []
    monkeypatch.setattr(fetch, "sleep", waits.append)
    return waits


@pytest.fixture
def home(tmp_path):
    return tmp_path / "home"
