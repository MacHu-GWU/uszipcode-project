#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
extract federalgovernmentzipcodes.zip and zcta2010.zip, find 
free-zipcode-database-Primary.csv and zcta2010.csv, put it with this script.

And run step1, step2, step3, then you get the zipcode sqlite database for 
uszipcode 0.0.8.
"""

from __future__ import print_function
from geomate.tests import GOOGLE_API_KEYS
from pprint import pprint as ppt
import pandas as pd
import geomate

df = pd.read_csv("free-zipcode-database-Primary.csv", dtype={"Zipcode": str})
todo = df["Zipcode"].tolist() # 42522 zipcode

googlegeocoder = geomate.GoogleGeocoder(api_keys=GOOGLE_API_KEYS)
googlegeocoder.set_sleeptime(0.1)
batch = geomate.BatchGeocoder(googlegeocoder, db_file="geocode.sqlite3")
batch.process_this(todo, shuffle=True)