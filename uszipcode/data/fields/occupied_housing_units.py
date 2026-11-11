# -*- coding: utf-8 -*-

"""``occupied_housing_units``. Claimed by ``census-dhc``. Vacant units are in ``housing_occupancy_vacant``."""

from ..core import Field, column, parse_int

FIELDS = (
    Field(
        name="occupied_housing_units",
        dtype=int,
        description="Occupied housing units in the ZCTA, 2020 Census DHC table H3 (H3_002N)",
        unit="units",
        extract=column("H3_002N", parse_int),
        examples=(({"H3_002N": "8178"}, 8178), ({"H3_002N": None}, None)),
    ),
)
