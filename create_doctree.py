#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from docfly import Docfly
import shutil
 
try:
    shutil.rmtree(r"source\uszipcode")
except Exception as e:
    print(e)
     
docfly = Docfly("uszipcode", dst="source", 
    ignore=[
        "uszipcode.packages",
        "uszipcode.tests.test_fuzzywuzzy.py",
        "uszipcode.tests.test_haversine.py"
    ]
)
docfly.fly()
