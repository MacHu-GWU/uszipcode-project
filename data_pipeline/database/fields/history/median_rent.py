# -*- coding: utf-8 -*-

"""``median_rent`` (gross rent) and its margin of error, history. Claimed by ``census-acs5-history``."""

from ...core import Field, census_int, column

FIELDS = (
    Field(
        name="median_rent",
        dtype=int,
        description="Median gross rent of renter-occupied units paying cash rent in the ZCTA, ACS 5-year estimate "
                    "ending in that year, in dollars of that year, table B25064 (B25064_001E)",
        unit="dollars",
        extract=column("B25064_001E", census_int),
        examples=(({"year": 2011, "B25064_001E": "1659"}, 1659), ({"year": 2011, "B25064_001E": "-666666666"}, None)),
    ),
    Field(
        name="median_rent_moe",
        dtype=int,
        description="Margin of error (90%) of median_rent (B25064_001M)",
        unit="dollars",
        extract=column("B25064_001M", census_int),
        examples=(({"year": 2011, "B25064_001M": "152"}, 152), ({"year": 2014, "B25064_001M": "-555555555"}, None)),
    ),
)
