# -*- coding: utf-8 -*-

"""
``zipcode_type``. Claimed by ``zip-basics``.

No free government source has the USPS class of a ZIP, so the value comes from
uszipcode 2.x as it is, and ZIPs newer than 2.x have no value.
"""

from ..core import Field, first_value

FIELDS = (
    Field(
        name="zipcode_type",
        dtype=str,
        description="STANDARD, PO BOX, UNIQUE or MILITARY, from uszipcode 2.x (not a government source)",
        extract=first_value("v2_zipcode_type"),
        examples=(({"v2_zipcode_type": "PO BOX", "hud_city": "WASHINGTON"}, "PO BOX"), ({"hud_city": "PHOENIX"}, None)),
    ),
)
