#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uszipcode.packages.fuzzywuzzy import process


def test_all():
    text = "playboy"
    choice = ["a cow boy", "play boy", "playboy magazine"]
    res = process.extract(text, choice)
    assert res[0][0] == "play boy"
    assert res[1][0] == "playboy magazine"
    assert res[2][0] == "a cow boy"


#--- Unittest ---
if __name__ == "__main__":
    import py
    import os
    py.test.cmdline.main("%s --tb=native -s" % os.path.basename(__file__))