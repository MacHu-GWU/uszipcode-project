# -*- coding: utf-8 -*-

"""
``population_by_race_*``. Claimed by ``census-dhc``.

Population by race (one race alone, or two or more); universe: total population. One column per bucket, each
the sum of its DHC variables. The buckets are those of the research, checked
against reference values (issue #88).
"""

from ..core import field_group

FIELDS = field_group("population_by_race", "2020 Census DHC table P3, ZCTA", "people", (
    ("white", "White alone", ("P3_002N",)),
    ("black", "Black or African American alone", ("P3_003N",)),
    ("aian", "American Indian and Alaska Native alone", ("P3_004N",)),
    ("asian", "Asian alone", ("P3_005N",)),
    ("nhpi", "Native Hawaiian and Other Pacific Islander alone", ("P3_006N",)),
    ("other", "Some Other Race alone", ("P3_007N",)),
    ("two_or_more", "Two or More Races", ("P3_008N",)),
))
