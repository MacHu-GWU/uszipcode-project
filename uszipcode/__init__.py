#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
try:
    from .searchengine import ZipcodeSearchEngine
except Exception as e:
    print(e)
    

__version__ = "0.1.3"
__short_description__ = ("USA zipcode programmable database, includes "
                         "up-to-date census and geometry information.")
__license__ = "MIT"
__author__ = "Sanhe Hu"
