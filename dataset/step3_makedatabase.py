#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from pprint import pprint as ppt
from sqlite4dummy import *
import pandas as pd

engine = Sqlite3Engine("geocode.sqlite3")
metadata = MetaData()