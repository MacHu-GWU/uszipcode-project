# -*- coding: utf-8 -*-

"""
The history catalog: one module per history Field. ``HISTORY_FIELDS`` is the list
of columns of the table ``zipcode_history``, one row per PK and year, next to
``zipcode`` and ``year``. History crawlers claim these Fields; the modules follow the
rules of ``fields/`` (``FIELDS``, named after the Field, import only ``core``).

Comparing years needs care, and the descriptions say so:

- the year of an ACS value is the last year of its 5-year window, and neighbouring
  windows share four years; dollars are dollars of that year, not adjusted;
- ZCTA boundaries change: ACS years up to 2020 use the 2010 ZCTAs, later years the
  2020 ZCTAs, and each census uses its own, so a code can stand for a different area.
"""

from . import census_population, acs_population, median_household_income, median_home_value, median_rent

#: every module of this folder, in column order; ``check`` fails if one is left out (rule L1)
MODULES = (census_population, acs_population, median_household_income, median_home_value, median_rent)

HISTORY_FIELDS = [field for module in MODULES for field in module.FIELDS]
