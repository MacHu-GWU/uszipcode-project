# -*- coding: utf-8 -*-

"""``median_household_income`` and its margin of error, history. Claimed by ``census-acs5-history``."""

from ...core import Field, census_int, column

FIELDS = (
    Field(
        name="median_household_income",
        dtype=int,
        description="Median household income of the ZCTA, ACS 5-year estimate ending in that year, in dollars of that "
                    "year, table B19013 (B19013_001E)",
        unit="dollars",
        extract=column("B19013_001E", census_int),
        examples=(({"year": 2011, "B19013_001E": "78081"}, 78081), ({"year": 2011, "B19013_001E": "-666666666"}, None)),
    ),
    Field(
        name="median_household_income_moe",
        dtype=int,
        description="Margin of error (90%) of median_household_income (B19013_001M)",
        unit="dollars",
        extract=column("B19013_001M", census_int),
        examples=(({"year": 2011, "B19013_001M": "9699"}, 9699), ({"year": 2011, "B19013_001M": "-222222222"}, None)),
    ),
)
