# -*- coding: utf-8 -*-

"""
``monthly_rent_including_utilities_*``. Claimed by ``census-acs5``.

Renter units with cash rent by bedrooms and gross rent band (native ACS bands); universe:
renter-occupied units. One column per bucket, each the sum of its ACS variables. The buckets are
those of the research, checked against reference values (issue #88).

Stands for the 2.x field(s) ``monthly_rent_including_utilities_studio_apt, _1_b, _2_b,
_3plus_b``.
"""

from ..core import census_int, field_group

FIELDS = field_group("monthly_rent_including_utilities", "latest ACS 5-year table B25068, ZCTA", "units", (
    ("studio_lt300", "No bedroom, Less than $300", ("B25068_004E",)),
    ("studio_300_499", "No bedroom, $300 to $499", ("B25068_005E",)),
    ("studio_500_749", "No bedroom, $500 to $749", ("B25068_006E",)),
    ("studio_750_999", "No bedroom, $750 to $999", ("B25068_007E",)),
    ("studio_1000_1499", "No bedroom, $1,000 to $1,499", ("B25068_008E",)),
    ("studio_1500_plus", "No bedroom, $1,500 or more", ("B25068_009E",)),
    ("studio_no_cash_rent", "No bedroom, no cash rent", ("B25068_010E",)),
    ("1br_lt300", "1 bedroom, Less than $300", ("B25068_013E",)),
    ("1br_300_499", "1 bedroom, $300 to $499", ("B25068_014E",)),
    ("1br_500_749", "1 bedroom, $500 to $749", ("B25068_015E",)),
    ("1br_750_999", "1 bedroom, $750 to $999", ("B25068_016E",)),
    ("1br_1000_1499", "1 bedroom, $1,000 to $1,499", ("B25068_017E",)),
    ("1br_1500_plus", "1 bedroom, $1,500 or more", ("B25068_018E",)),
    ("1br_no_cash_rent", "1 bedroom, no cash rent", ("B25068_019E",)),
    ("2br_lt300", "2 bedrooms, Less than $300", ("B25068_022E",)),
    ("2br_300_499", "2 bedrooms, $300 to $499", ("B25068_023E",)),
    ("2br_500_749", "2 bedrooms, $500 to $749", ("B25068_024E",)),
    ("2br_750_999", "2 bedrooms, $750 to $999", ("B25068_025E",)),
    ("2br_1000_1499", "2 bedrooms, $1,000 to $1,499", ("B25068_026E",)),
    ("2br_1500_plus", "2 bedrooms, $1,500 or more", ("B25068_027E",)),
    ("2br_no_cash_rent", "2 bedrooms, no cash rent", ("B25068_028E",)),
    ("3br_plus_lt300", "3 or more bedrooms, Less than $300", ("B25068_031E",)),
    ("3br_plus_300_499", "3 or more bedrooms, $300 to $499", ("B25068_032E",)),
    ("3br_plus_500_749", "3 or more bedrooms, $500 to $749", ("B25068_033E",)),
    ("3br_plus_750_999", "3 or more bedrooms, $750 to $999", ("B25068_034E",)),
    ("3br_plus_1000_1499", "3 or more bedrooms, $1,000 to $1,499", ("B25068_035E",)),
    ("3br_plus_1500_plus", "3 or more bedrooms, $1,500 or more", ("B25068_036E",)),
    ("3br_plus_no_cash_rent", "3 or more bedrooms, no cash rent", ("B25068_037E",)),
), convert=census_int)
