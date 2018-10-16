#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
``uszipcode`` is awesome!
"""

from __future__ import print_function

try:
    from .search import (
        SearchEngine, SimpleZipcode, Zipcode, ZipcodeType, SORT_BY_DIST,
    )
except Exception as e:  # pragma: no cover
    print(e)

__version__ = "0.2.2"
__short_description__ = ("USA zipcode programmable database, includes "
                         "up-to-date census and geometry information.")
__license__ = "MIT"
__author__ = "Sanhe Hu"
__author_email__ = "husanhe@gmail.com"
__maintainer__ = "Sanhe Hu"
__maintainer_email__ = "husanhe@gmail.com"
__github_username__ = "MacHu-GWU"
