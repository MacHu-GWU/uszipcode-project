# -*- coding: utf-8 -*-

"""
The history catalog: one module per history Field. A history crawler has one row
per ZIP and year and claims these Fields. In the database, a history Field ``x`` is
the column ``x_by_year`` of the main table: the values of the ZIP by year, as JSON
(``{"2011": 13642, "2012": 14304}``). The modules follow the rules of ``fields/``
(``FIELDS``, named after the Field, import only ``core``).

Comparing years needs care, and the descriptions say so:

- the year of an ACS value is the last year of its 5-year window, and neighbouring
  windows share four years; dollars are dollars of that year, not adjusted;
- ZCTA boundaries change: ACS years up to 2020 use the 2010 ZCTAs, later years the
  2020 ZCTAs, and each census uses its own, so a code can stand for a different area;
- the year of an IRS value is the tax year, and its ZIP is the one on the tax return.
"""

from . import (
    census_population, acs_population, median_household_income, median_home_value, median_rent,
    tax_returns, people_on_tax_returns, average_income_per_return,
)

#: every module of this folder, in column order; ``check`` fails if one is left out (rule L1)
MODULES = (census_population, acs_population, median_household_income, median_home_value, median_rent,
           tax_returns, people_on_tax_returns, average_income_per_return)

HISTORY_FIELDS = [field for module in MODULES for field in module.FIELDS]
