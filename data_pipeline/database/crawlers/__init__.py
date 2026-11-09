# -*- coding: utf-8 -*-

"""
The crawlers: one module per data source. ``CRAWLERS`` is the registry.

A crawler module defines ``CRAWLER``: its name, the Fields it claims (by their
modules, with ``field_names``), the files it downloads and a ``parse()`` that turns
those files into source rows. It imports only ``..core``, ``..fields`` and
``...zipcodes``: it cannot open a URL and never reads a value itself.
"""

from . import (
    census_gazetteer, census_dhc, census_acs5, irs_soi, zip_basics, census_acs5_history, census_decennial, zcta_geometry,
)

#: every module of this folder; ``check`` fails if one is left out (rule L1).
#: History crawlers (``history=True``) fill the history table and claim from ``HISTORY_FIELDS``.
MODULES = (census_gazetteer, census_dhc, census_acs5, irs_soi, zip_basics, census_acs5_history, census_decennial,
           zcta_geometry)

#: every crawler, in the order ``crawl --all`` runs them
CRAWLERS = [m.CRAWLER for m in MODULES]
