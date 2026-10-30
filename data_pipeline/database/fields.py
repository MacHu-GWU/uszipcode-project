# -*- coding: utf-8 -*-

"""
The Field catalog: the one list of all columns of the database, in column order.

Every Field here must be claimed by exactly one crawler (``python -m
data_pipeline.database check`` verifies it). Names follow the 2.x column names
where the meaning is the same. Census values are tabulated by ZCTA, so the
descriptions say "ZCTA".
"""

from .core import Field

FIELDS = [
    Field("lat", float, "Latitude of the ZCTA internal point (Census Gazetteer INTPTLAT)", "degrees"),
    Field("lng", float, "Longitude of the ZCTA internal point (Census Gazetteer INTPTLONG)", "degrees"),
    Field("land_area_in_sqmi", float, "Land area of the ZCTA (Census Gazetteer ALAND_SQMI)", "sq mi"),
    Field("population", int, "Total population of the ZCTA, 2020 Census DHC table P1 (P1_001N)", "people"),
    Field("housing_units", int, "Housing units in the ZCTA, 2020 Census DHC table H1 (H1_001N)", "units"),
]
