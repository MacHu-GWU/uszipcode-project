# -*- coding: utf-8 -*-

"""
``county``. Claimed by ``zip-basics``.

A ZIP can span several counties; this is the one with most of its residential
addresses (see ``crawlers/zip_basics.py``).
"""

from ..core import Field, first_value

FIELDS = (
    Field(
        name="county",
        dtype=str,
        description="Main county of the ZIP: HUD-USPS crosswalk with the Census Gazetteer county name, else uszipcode 2.x",
        extract=first_value("hud_county_name", "v2_county"),
        examples=(
            ({"hud_county_name": "New York County", "v2_county": "New York County"}, "New York County"),
            ({"hud_county_fips": "48", "v2_county": "Montgomery County"}, "Montgomery County"),
            ({}, None),
        ),
    ),
)
