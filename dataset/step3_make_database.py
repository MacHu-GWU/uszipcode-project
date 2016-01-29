#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cconstruct a zipcode sqlite database for uszipcode extension.
"""

from __future__ import print_function
from pprint import pprint as ppt
from sqlite4dummy import *
import pandas as pd

df = pd.read_csv("zipcode.txt", sep="\t")
engine = Sqlite3Engine("zipcode.sqlite3")
metadata = MetaData()
zipcode_table = Table("zipcode", metadata,
    Column("Zipcode", dtype.TEXT, primary_key=True),
    Column("ZipCodeType", dtype.TEXT),
    Column("City", dtype.TEXT),
    Column("State", dtype.TEXT),
    Column("POPULATION", dtype.INTEGER),
    Column("Density", dtype.REAL),
    Column("TotalWages", dtype.REAL),
    Column("Wealthy", dtype.REAL),
    Column("HouseOfUnits", dtype.INTEGER),
    Column("LandArea", dtype.REAL),
    Column("WaterArea", dtype.REAL),
    Column("Latitude", dtype.REAL),
    Column("Longitude", dtype.REAL),
    Column("NEBoundLatitude", dtype.REAL),
    Column("NEBoundLongitude", dtype.REAL),
    Column("SWBoundLatitude", dtype.REAL),
    Column("SWBoundLongitude", dtype.REAL),
)
metadata.create_all(engine)
engine.insert_many_record(zipcode_table.insert(), df.values.tolist())
engine.commit()