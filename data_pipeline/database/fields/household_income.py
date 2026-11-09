# -*- coding: utf-8 -*-

"""
``household_income_*``. Claimed by ``census-acs5``.

Households by income band (ACS bands merged); universe: households. One column per bucket, each
the sum of its ACS variables. The buckets are those of the research, checked against reference
values (issue #88).
"""

from ..core import census_int, field_group

FIELDS = field_group("household_income", "latest ACS 5-year table B19001, ZCTA", "households", (
    ("lt25k", "Under $25,000", ("B19001_002E", "B19001_003E", "B19001_004E", "B19001_005E")),
    ("25k_44k", "$25,000 to $44,999", ("B19001_006E", "B19001_007E", "B19001_008E", "B19001_009E")),
    ("45k_59k", "$45,000 to $59,999", ("B19001_010E", "B19001_011E")),
    ("60k_99k", "$60,000 to $99,999", ("B19001_012E", "B19001_013E")),
    ("100k_149k", "$100,000 to $149,999", ("B19001_014E", "B19001_015E")),
    ("150k_199k", "$150,000 to $199,999", ("B19001_016E",)),
    ("200k_plus", "$200,000 or more", ("B19001_017E",)),
), convert=census_int)
