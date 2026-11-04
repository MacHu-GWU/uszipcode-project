# -*- coding: utf-8 -*-

"""``housing_units``. Claimed by ``census-dhc``."""

from ..core import Field, column, parse_int

FIELDS = (
    Field(
        name="housing_units",
        dtype=int,
        description="Housing units in the ZCTA, 2020 Census DHC table H1 (H1_001N)",
        unit="units",
        extract=column("H1_001N", parse_int),
        examples=(({"H1_001N": "18926"}, 18926), ({"H1_001N": "0"}, 0), ({"H1_001N": None}, None)),
    ),
)
