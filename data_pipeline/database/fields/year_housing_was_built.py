# -*- coding: utf-8 -*-

"""
``year_housing_was_built_*``. Claimed by ``census-acs5``.

Housing units by decade built; universe: housing units. One column per bucket, each the sum of
its ACS variables. The buckets are those of the research, checked against reference values
(issue #88).
"""

from ..core import census_int, field_group

FIELDS = field_group("year_housing_was_built", "latest ACS 5-year table B25034, ZCTA", "units", (
    ("2020_plus", "2020 or later", ("B25034_002E",)),
    ("2010s", "2010 to 2019", ("B25034_003E",)),
    ("2000s", "2000 to 2009", ("B25034_004E",)),
    ("1990s", "1990 to 1999", ("B25034_005E",)),
    ("1980s", "1980 to 1989", ("B25034_006E",)),
    ("1970s", "1970 to 1979", ("B25034_007E",)),
    ("1960s", "1960 to 1969", ("B25034_008E",)),
    ("1950s", "1950 to 1959", ("B25034_009E",)),
    ("1940s", "1940 to 1949", ("B25034_010E",)),
    ("1939_or_earlier", "1939 or earlier", ("B25034_011E",)),
), convert=census_int)
