# -*- coding: utf-8 -*-

"""
``major_city``. Claimed by ``zip-basics``.

Upper case, as HUD and ZBP write it. 2.x stored title case; converting needs care
(McKINNEY, ST. LOUIS), so it is left to the library.
"""

from ..core import Field, first_value, upper_text

FIELDS = (
    Field(
        name="major_city",
        dtype=str,
        simple=True,
        description="USPS preferred city of the ZIP: HUD-USPS crosswalk, else Census ZBP, else uszipcode 2.x",
        extract=first_value("hud_city", "zbp_city", "v2_city", convert=upper_text),
        examples=(
            ({"hud_city": "NEW YORK", "zbp_city": "NYC", "v2_city": "New York"}, "NEW YORK"),
            ({"zbp_city": "HOLTSVILLE", "v2_city": "Holtsville"}, "HOLTSVILLE"),
            ({"v2_city": "Apo"}, "APO"),
            ({}, None),
        ),
    ),
)
