# -*- coding: utf-8 -*-

"""``median_rent`` (gross rent: contract rent plus utilities) and its margin of error. Claimed by ``census-acs5``."""

from ..core import Field, census_int, column

FIELDS = (
    Field(
        name="median_rent",
        dtype=int,
        description="Median gross rent of renter-occupied units paying cash rent in the ZCTA, latest ACS 5-year table B25064 (B25064_001E)",
        unit="dollars",
        extract=column("B25064_001E", census_int),
        examples=(({"B25064_001E": "2420"}, 2420), ({"B25064_001E": "-666666666"}, None)),
    ),
    Field(
        name="median_rent_moe",
        dtype=int,
        description="Margin of error (90%) of median_rent (B25064_001M)",
        unit="dollars",
        extract=column("B25064_001M", census_int),
        examples=(({"B25064_001M": "119"}, 119), ({"B25064_001M": "-222222222"}, None)),
    ),
)
