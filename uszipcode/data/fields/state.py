# -*- coding: utf-8 -*-

"""``state``. Claimed by ``zip-basics``."""

from ..core import Field, first_value, upper_text

FIELDS = (
    Field(
        name="state",
        dtype=str,
        simple=True,
        description="Two-letter state of the ZIP: HUD-USPS crosswalk, else Census ZBP, else uszipcode 2.x",
        extract=first_value("hud_state", "zbp_state", "v2_state", convert=upper_text),
        examples=(
            ({"hud_state": "DC", "zbp_state": "VA", "v2_state": "MD"}, "DC"),
            ({"zbp_state": "NY"}, "NY"),
            ({"v2_state": "ae"}, "AE"),
            ({}, None),
        ),
    ),
)
