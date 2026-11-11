# -*- coding: utf-8 -*-

"""
``school_enrollment_age_3_to_17_*``. Claimed by ``census-acs5``.

Population aged 3 to 17 by school type (both sexes, four age groups added); universe: population
3 to 17 years. One column per bucket, each the sum of its ACS variables. The buckets are those
of the research, checked against reference values (issue #88).
"""

from ..core import census_int, field_group

FIELDS = field_group("school_enrollment_age_3_to_17", "latest ACS 5-year table B14003, ZCTA", "people", (
    ("public", "Enrolled in public school", ("B14003_004E", "B14003_005E", "B14003_006E", "B14003_007E", "B14003_032E", "B14003_033E", "B14003_034E", "B14003_035E")),
    ("private", "Enrolled in private school", ("B14003_013E", "B14003_014E", "B14003_015E", "B14003_016E", "B14003_041E", "B14003_042E", "B14003_043E", "B14003_044E")),
    ("not_enrolled", "Not enrolled in school", ("B14003_022E", "B14003_023E", "B14003_024E", "B14003_025E", "B14003_050E", "B14003_051E", "B14003_052E", "B14003_053E")),
), convert=census_int)
