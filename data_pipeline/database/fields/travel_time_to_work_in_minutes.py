# -*- coding: utf-8 -*-

"""
``travel_time_to_work_in_minutes_*``. Claimed by ``census-acs5``.

Workers 16+ not working at home by travel time to work; universe: workers 16+ not working at
home. One column per bucket, each the sum of its ACS variables. The buckets are those of the
research, checked against reference values (issue #88).
"""

from ..core import census_int, field_group

FIELDS = field_group("travel_time_to_work_in_minutes", "latest ACS 5-year table B08303, ZCTA", "workers", (
    ("lt10", "Under 10 minutes", ("B08303_002E", "B08303_003E")),
    ("10_19", "10 to 19 minutes", ("B08303_004E", "B08303_005E")),
    ("20_29", "20 to 29 minutes", ("B08303_006E", "B08303_007E")),
    ("30_39", "30 to 39 minutes", ("B08303_008E", "B08303_009E")),
    ("40_44", "40 to 44 minutes", ("B08303_010E",)),
    ("45_59", "45 to 59 minutes", ("B08303_011E",)),
    ("60_89", "60 to 89 minutes", ("B08303_012E",)),
    ("90_plus", "90 or more minutes", ("B08303_013E",)),
), convert=census_int)
