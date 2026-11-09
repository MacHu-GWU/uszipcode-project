# -*- coding: utf-8 -*-

"""
``median_household_income`` and its margin of error. Claimed by ``census-acs5``.

Values above $250,000 are top-coded by the Census as 250001.
"""

from ..core import Field, census_int, column

FIELDS = (
    Field(
        name="median_household_income",
        dtype=int,
        description="Median household income in the ZCTA, latest ACS 5-year table B19013 (B19013_001E)",
        unit="dollars",
        extract=column("B19013_001E", census_int),
        examples=(({"B19013_001E": "98917"}, 98917), ({"B19013_001E": "-666666666"}, None)),
    ),
    Field(
        name="median_household_income_moe",
        dtype=int,
        description="Margin of error (90%) of median_household_income (B19013_001M)",
        unit="dollars",
        extract=column("B19013_001M", census_int),
        examples=(({"B19013_001M": "13066"}, 13066), ({"B19013_001M": "-222222222"}, None)),
    ),
)
