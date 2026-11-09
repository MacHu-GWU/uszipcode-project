# -*- coding: utf-8 -*-

"""``median_home_value`` and its margin of error, history. Claimed by ``census-acs5-history``."""

from ...core import Field, census_int, column

FIELDS = (
    Field(
        name="median_home_value",
        dtype=int,
        description="Median value of owner-occupied housing units in the ZCTA, ACS 5-year estimate ending in that year, "
                    "in dollars of that year, table B25077 (B25077_001E); the top code changed over the years",
        unit="dollars",
        extract=column("B25077_001E", census_int),
        examples=(({"year": 2011, "B25077_001E": "546500"}, 546500), ({"year": 2011, "B25077_001E": "-666666666"}, None)),
    ),
    Field(
        name="median_home_value_moe",
        dtype=int,
        description="Margin of error (90%) of median_home_value (B25077_001M)",
        unit="dollars",
        extract=column("B25077_001M", census_int),
        examples=(({"year": 2011, "B25077_001M": "51353"}, 51353), ({"year": 2011, "B25077_001M": "-222222222"}, None)),
    ),
)
