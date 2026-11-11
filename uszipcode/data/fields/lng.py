# -*- coding: utf-8 -*-

"""``lng``. Claimed by ``census-gazetteer``."""

from ..core import Field, column, parse_float

FIELDS = (
    Field(
        name="lng",
        dtype=float,
        simple=True,
        description="Longitude of the ZCTA internal point (Census Gazetteer INTPTLONG)",
        unit="degrees",
        extract=column("INTPTLONG", parse_float),
        examples=(({"INTPTLONG": "-73.997298"}, -73.997298), ({"INTPTLONG": ""}, None)),
    ),
)
