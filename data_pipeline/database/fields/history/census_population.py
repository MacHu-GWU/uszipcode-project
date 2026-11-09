# -*- coding: utf-8 -*-

"""``census_population``, history. Claimed by ``census-decennial``."""

from ...core import Field, census_int, first_value

FIELDS = (
    Field(
        name="census_population",
        dtype=int,
        description="Population of the ZCTA counted by the decennial census of that year "
                    "(2000 and 2010: Summary File 1 P001001; 2020: DHC P1_001N); each census has its own ZCTAs",
        unit="people",
        extract=first_value("P001001", "P1_001N", convert=census_int),
        examples=(({"year": 2010, "P001001": "14642"}, 14642), ({"year": 2020, "P1_001N": "14945"}, 14945),
                  ({"year": 2000}, None)),
    ),
)
