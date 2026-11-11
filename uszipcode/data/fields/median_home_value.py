# -*- coding: utf-8 -*-

"""
``median_home_value`` and its margin of error. Claimed by ``census-acs5``.

Values above $2,000,000 are top-coded by the Census as 2000001.
"""

from ..core import Field, census_int, column

FIELDS = (
    Field(
        name="median_home_value",
        dtype=int,
        simple=True,
        description="Median value of owner-occupied housing units in the ZCTA, latest ACS 5-year table B25077 (B25077_001E)",
        unit="dollars",
        extract=column("B25077_001E", census_int),
        examples=(({"B25077_001E": "743700"}, 743700), ({"B25077_001E": "-666666666"}, None)),
    ),
    Field(
        name="median_home_value_moe",
        dtype=int,
        description="Margin of error (90%) of median_home_value (B25077_001M)",
        unit="dollars",
        extract=column("B25077_001M", census_int),
        examples=(({"B25077_001M": "108570"}, 108570), ({"B25077_001M": "-222222222"}, None)),
    ),
)
