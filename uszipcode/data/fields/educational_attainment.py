# -*- coding: utf-8 -*-

"""
``educational_attainment_*``. Claimed by ``census-acs5``.

Population 25+ by highest level of education; universe: population 25 years and over. One column
per bucket, each the sum of its ACS variables. The buckets are those of the research, checked
against reference values (issue #88).

Stands for the 2.x field(s) ``educational_attainment_for_population_25_and_over``.
"""

from ..core import census_int, field_group

FIELDS = field_group("educational_attainment", "latest ACS 5-year table B15003, ZCTA", "people", (
    ("less_than_high_school", "Less than high school diploma", ("B15003_002E", "B15003_003E", "B15003_004E", "B15003_005E", "B15003_006E", "B15003_007E", "B15003_008E", "B15003_009E", "B15003_010E", "B15003_011E", "B15003_012E", "B15003_013E", "B15003_014E", "B15003_015E", "B15003_016E")),
    ("high_school_or_ged", "High school diploma or GED", ("B15003_017E", "B15003_018E")),
    ("some_college_no_degree", "Some college, no degree", ("B15003_019E", "B15003_020E")),
    ("associate", "Associate's degree", ("B15003_021E",)),
    ("bachelor", "Bachelor's degree", ("B15003_022E",)),
    ("master", "Master's degree", ("B15003_023E",)),
    ("professional", "Professional school degree", ("B15003_024E",)),
    ("doctorate", "Doctorate degree", ("B15003_025E",)),
), convert=census_int)
