# -*- coding: utf-8 -*-

"""
The crawlers: one module per data source. ``CRAWLERS`` is the registry.

A crawler module defines ``CRAWLER``: its name, the Fields it claims, the files it
downloads and a ``parse()`` that turns those files into source rows. It imports
only ``..core`` and ``...zipcodes``: it cannot open a URL and does not know how a
Field is read.
"""

from . import census_gazetteer, census_dhc, zip_basics

#: every module of this folder; ``check`` fails if one is left out (rule L1)
MODULES = (census_gazetteer, census_dhc, zip_basics)

#: every crawler, in the order ``crawl --all`` runs them
CRAWLERS = [m.CRAWLER for m in MODULES]
