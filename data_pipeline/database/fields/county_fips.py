# -*- coding: utf-8 -*-

"""
``county_fips``. Claimed by ``zip-basics``.

The 5-digit state + county code of the main county. HUD writes an incomplete code
for a few ZIPs (``48`` for 77352); those get no value.
"""

from ..core import Field, first_value


def _five_digits(code: str):
    code = code.strip()
    return code if len(code) == 5 and code.isdigit() else None


FIELDS = (
    Field(
        name="county_fips",
        dtype=str,
        description="FIPS code (state + county) of the main county of the ZIP, HUD-USPS crosswalk",
        extract=first_value("hud_county_fips", convert=_five_digits),
        examples=(({"hud_county_fips": "36061"}, "36061"), ({"hud_county_fips": "48"}, None), ({}, None)),
    ),
)
