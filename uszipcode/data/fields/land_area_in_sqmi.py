# -*- coding: utf-8 -*-

"""``land_area_in_sqmi``. Claimed by ``zip-basics``."""

from ..core import Field, column, parse_float

FIELDS = (
    Field(
        name="land_area_in_sqmi",
        dtype=float,
        simple=True,
        description="Land area of the ZCTA (Census Gazetteer ALAND_SQMI)",
        unit="sq mi",
        extract=column("ALAND_SQMI", parse_float),
        examples=(({"ALAND_SQMI": "0.624"}, 0.624), ({"ALAND_SQMI": ""}, None)),
    ),
)
