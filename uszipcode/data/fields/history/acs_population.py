# -*- coding: utf-8 -*-

"""``acs_population`` and its margin of error, history. Claimed by ``census-acs5-history``."""

from ...core import Field, census_int, column

FIELDS = (
    Field(
        name="acs_population",
        dtype=int,
        description="Total population of the ZCTA, ACS 5-year estimate ending in that year, table B01003 (B01003_001E)",
        unit="people",
        extract=column("B01003_001E", census_int),
        examples=(({"year": 2015, "B01003_001E": "15687"}, 15687), ({"year": 2015, "B01003_001E": "-666666666"}, None)),
    ),
    Field(
        name="acs_population_moe",
        dtype=int,
        description="Margin of error (90%) of acs_population (B01003_001M)",
        unit="people",
        extract=column("B01003_001M", census_int),
        examples=(({"year": 2011, "B01003_001M": "1171"}, 1171), ({"year": 2011, "B01003_001M": "-555555555"}, None)),
    ),
)
