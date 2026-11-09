# -*- coding: utf-8 -*-

"""
``owner_occupied_home_values_*``. Claimed by ``census-acs5``.

Owner-occupied housing units by value band (lower bands merged, upper bands native); universe:
owner-occupied housing units. One column per bucket, each the sum of its ACS variables. The
buckets are those of the research, checked against reference values (issue #88).
"""

from ..core import census_int, field_group

FIELDS = field_group("owner_occupied_home_values", "latest ACS 5-year table B25075, ZCTA", "units", (
    ("lt100k", "Under $100,000", ("B25075_002E", "B25075_003E", "B25075_004E", "B25075_005E", "B25075_006E", "B25075_007E", "B25075_008E", "B25075_009E", "B25075_010E", "B25075_011E", "B25075_012E", "B25075_013E", "B25075_014E")),
    ("100k_149k", "$100,000 to $149,999", ("B25075_015E", "B25075_016E")),
    ("150k_199k", "$150,000 to $199,999", ("B25075_017E", "B25075_018E")),
    ("200k_299k", "$200,000 to $299,999", ("B25075_019E", "B25075_020E")),
    ("300k_399k", "$300,000 to $399,999", ("B25075_021E",)),
    ("400k_499k", "$400,000 to $499,999", ("B25075_022E",)),
    ("500k_749k", "$500,000 to $749,999", ("B25075_023E",)),
    ("750k_999k", "$750,000 to $999,999", ("B25075_024E",)),
    ("1m_1_5m", "$1,000,000 to $1,499,999", ("B25075_025E",)),
    ("1_5m_2m", "$1,500,000 to $1,999,999", ("B25075_026E",)),
    ("2m_plus", "$2,000,000 or more", ("B25075_027E",)),
), convert=census_int)
