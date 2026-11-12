# -*- coding: utf-8 -*-

"""
The crawlers: one module per data source. ``CRAWLERS`` is the registry.

A crawler module defines ``CRAWLER``: its name, the Fields it claims (by their
modules, with ``field_names``), the files it downloads and a ``parse()`` that turns
those files into source rows. It imports only ``..core``, ``..fields``, ``..keys``
and ``..zipcodes``: it cannot open a URL and never reads a value itself.
"""

from . import (
    zip_basics, census_dhc, census_acs5, irs_soi, census_acs5_history, census_decennial, irs_soi_history,
    zcta_geometry,
)

#: every module of this folder; ``check`` fails if one is left out (rule L1).
#: History crawlers (``history=True``) have one row per ZIP and year and claim from ``HISTORY_FIELDS``.
MODULES = (zip_basics, census_dhc, census_acs5, irs_soi, census_acs5_history, census_decennial, irs_soi_history,
           zcta_geometry)

#: every crawler, in the order ``crawl --all`` runs them
CRAWLERS = [m.CRAWLER for m in MODULES]
