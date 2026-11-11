# -*- coding: utf-8 -*-

"""``population``. Claimed by ``census-dhc``."""

from ..core import Field, column, parse_int

FIELDS = (
    Field(
        name="population",
        dtype=int,
        simple=True,
        description="Total population of the ZCTA, 2020 Census DHC table P1 (P1_001N)",
        unit="people",
        extract=column("P1_001N", parse_int),
        examples=(({"P1_001N": "32612"}, 32612), ({"P1_001N": "0"}, 0), ({"P1_001N": None}, None)),
    ),
)
