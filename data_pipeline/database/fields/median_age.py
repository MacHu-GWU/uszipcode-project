# -*- coding: utf-8 -*-

"""``median_age`` and its margin of error. Claimed by ``census-acs5``."""

from ..core import Field, census_float, column

FIELDS = (
    Field(
        name="median_age",
        dtype=float,
        description="Median age of the population of the ZCTA, latest ACS 5-year table B01002 (B01002_001E)",
        unit="years",
        extract=column("B01002_001E", census_float),
        examples=(({"B01002_001E": "31.3"}, 31.3), ({"B01002_001E": "-666666666"}, None)),
    ),
    Field(
        name="median_age_moe",
        dtype=float,
        description="Margin of error (90%) of median_age (B01002_001M)",
        unit="years",
        extract=column("B01002_001M", census_float),
        examples=(({"B01002_001M": "1.3"}, 1.3), ({"B01002_001M": "-222222222"}, None)),
    ),
)
