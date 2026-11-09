# -*- coding: utf-8 -*-

"""
``employment_status_*``. Claimed by ``census-acs5``.

Population 16+ by work experience in the past 12 months and earnings; universe: population 16
years and over. One column per bucket, each the sum of its ACS variables. The buckets are those
of the research, checked against reference values (issue #88).
"""

from ..core import census_int, field_group

FIELDS = field_group("employment_status", "latest ACS 5-year table B20005, ZCTA", "people", (
    ("full_time_year_round_with_earnings", "Worked full-time, year-round, with earnings", ("B20005_005E", "B20005_052E")),
    ("less_than_full_time_with_earnings", "Worked less than full-time or year-round, with earnings", ("B20005_028E", "B20005_075E")),
    ("no_earnings", "No earnings", ("B20005_004E", "B20005_027E", "B20005_051E", "B20005_074E")),
), convert=census_int)
