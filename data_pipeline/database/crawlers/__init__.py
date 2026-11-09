# -*- coding: utf-8 -*-

"""
The crawlers: one module per data source. ``CRAWLERS`` is the registry.

A crawler module defines ``CRAWLER``: its name, the Fields it claims (by their
modules, with ``field_names``), the files it downloads and a ``parse()`` that turns
those files into source rows. It imports only ``..core``, ``..fields`` and
``...zipcodes``: it cannot open a URL and never reads a value itself.
"""

from . import census_gazetteer, census_dhc, zip_basics

#: every module of this folder; ``check`` fails if one is left out (rule L1)
MODULES = (census_gazetteer, census_dhc, zip_basics)

#: every crawler, in the order ``crawl --all`` runs them
CRAWLERS = [m.CRAWLER for m in MODULES]
