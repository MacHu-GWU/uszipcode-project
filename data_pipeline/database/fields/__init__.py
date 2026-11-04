# -*- coding: utf-8 -*-

"""
The Field catalog: one module per Field. ``FIELDS`` is the one list of all columns
of the database, and its order is the column order.

A Field module defines ``FIELDS``: a tuple with its Field, or with many Fields
when a loop generates a group (one distribution, one column per number). The module
is named after its Field, or after the prefix its group shares. It imports only
``..core``: what a Field needs from a data source is the name of a source column.

Every Field must be claimed by exactly one crawler (``check`` verifies it). Names
follow the 2.x column names where the meaning is the same. Census values are
tabulated by ZCTA, so the descriptions say "ZCTA".
"""

from . import lat, lng, land_area_in_sqmi, population, housing_units

#: every module of this folder, in column order; ``check`` fails if one is left out (rule L1)
MODULES = (lat, lng, land_area_in_sqmi, population, housing_units)

FIELDS = [field for module in MODULES for field in module.FIELDS]
