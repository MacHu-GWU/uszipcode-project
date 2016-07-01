#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pytest
from uszipcode.searchengine import Zipcode, ZipcodeSearchEngine


def test_result_to_csv():
    with ZipcodeSearchEngine() as search:
        res = search.by_prefix("100")
        search.export_to_csv(res, "result.csv")

    try:
        os.remove("result.csv")
    except:
        pass


def test_all():
    with ZipcodeSearchEngine() as search:
        res = search.all()
        search.export_to_csv(res, "result.csv")
 
    try:
        os.remove("result.csv")
    except:
        pass

#--- Unittest ---
if __name__ == "__main__":
    import py
    import os
    py.test.cmdline.main("%s --tb=native -s" % os.path.basename(__file__))
