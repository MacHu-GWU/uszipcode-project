# -*- coding: utf-8 -*-

"""
The Field catalog: one module per Field. ``FIELDS`` is the one list of all columns
of the database, and its order is the column order.

A Field module defines ``FIELDS``: a tuple with its Field, or with many Fields
when ``field_group`` generates a group (one distribution, one column per number).
The module is named after its Field, or after the prefix its group shares. It
imports only ``..core``: what a Field needs from a data source is the name of a
source column. A crawler claims Fields by their modules (``field_names``).

Every Field must be claimed by exactly one crawler (``check`` verifies it). Names
follow the 2.x column names where the meaning is the same. Census values are
tabulated by ZCTA, so the descriptions say "ZCTA".
"""

from . import (
    zipcode_type, major_city, state, county, county_fips,
    lat, lng, land_area_in_sqmi, water_area_in_sqmi,
    population, population_by_gender, population_by_age, children_by_age, population_by_race,
    families_vs_singles, households_with_kids, head_of_household_by_age, housing_type,
    housing_units, occupied_housing_units, housing_occupancy, vacancy_reason,
)

#: every module of this folder, in column order; ``check`` fails if one is left out (rule L1)
MODULES = (
    zipcode_type, major_city, state, county, county_fips,
    lat, lng, land_area_in_sqmi, water_area_in_sqmi,
    population, population_by_gender, population_by_age, children_by_age, population_by_race,
    families_vs_singles, households_with_kids, head_of_household_by_age, housing_type,
    housing_units, occupied_housing_units, housing_occupancy, vacancy_reason,
)

FIELDS = [field for module in MODULES for field in module.FIELDS]
