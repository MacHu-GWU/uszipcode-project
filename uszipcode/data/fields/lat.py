# -*- coding: utf-8 -*-

"""``lat``. Claimed by ``census-gazetteer``."""

from ..core import Field, column, parse_float

FIELDS = (
    Field(
        name="lat",
        dtype=float,
        simple=True,
        description="Latitude of the ZCTA internal point (Census Gazetteer INTPTLAT)",
        unit="degrees",
        extract=column("INTPTLAT", parse_float),
        examples=(({"INTPTLAT": "40.750649"}, 40.750649), ({"INTPTLAT": ""}, None)),
    ),
)
