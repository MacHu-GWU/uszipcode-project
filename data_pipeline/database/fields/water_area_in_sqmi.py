# -*- coding: utf-8 -*-

"""``water_area_in_sqmi``. Claimed by ``census-gazetteer``."""

from ..core import Field, column, parse_float

FIELDS = (
    Field(
        name="water_area_in_sqmi",
        dtype=float,
        description="Water area of the ZCTA (Census Gazetteer AWATER_SQMI)",
        unit="sq mi",
        extract=column("AWATER_SQMI", parse_float),
        examples=(({"AWATER_SQMI": "0.231"}, 0.231), ({"AWATER_SQMI": "0."}, 0.0), ({"AWATER_SQMI": ""}, None)),
    ),
)
