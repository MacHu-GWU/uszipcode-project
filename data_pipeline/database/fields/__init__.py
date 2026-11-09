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
    population, population_density,
    population_by_gender, population_by_age, children_by_age, population_by_race, median_age,
    families_vs_singles, households_with_kids, head_of_household_by_age, housing_type,
    housing_units, occupied_housing_units, housing_occupancy, vacancy_reason,
    median_home_value, owner_occupied_home_values, year_housing_was_built,
    median_rent, rental_properties_by_number_of_rooms, monthly_rent_including_utilities,
    median_household_income, household_income, annual_individual_earnings, employment_status,
    sources_of_household_income, household_investment_income, household_retirement_income, poverty_rate,
    means_of_transportation_to_work, travel_time_to_work_in_minutes,
    educational_attainment, school_enrollment_age_3_to_17,
)

#: every module of this folder, in column order; ``check`` fails if one is left out (rule L1)
MODULES = (
    zipcode_type, major_city, state, county, county_fips,
    lat, lng, land_area_in_sqmi, water_area_in_sqmi,
    population, population_density,
    population_by_gender, population_by_age, children_by_age, population_by_race, median_age,
    families_vs_singles, households_with_kids, head_of_household_by_age, housing_type,
    housing_units, occupied_housing_units, housing_occupancy, vacancy_reason,
    median_home_value, owner_occupied_home_values, year_housing_was_built,
    median_rent, rental_properties_by_number_of_rooms, monthly_rent_including_utilities,
    median_household_income, household_income, annual_individual_earnings, employment_status,
    sources_of_household_income, household_investment_income, household_retirement_income, poverty_rate,
    means_of_transportation_to_work, travel_time_to_work_in_minutes,
    educational_attainment, school_enrollment_age_3_to_17,
)

FIELDS = [field for module in MODULES for field in module.FIELDS]
