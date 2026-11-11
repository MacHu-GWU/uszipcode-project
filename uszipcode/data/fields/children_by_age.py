# -*- coding: utf-8 -*-

"""
``children_by_age_*``. Claimed by ``census-dhc``.

Population by sex and single year of age, 0 to 20; universe: total population. One column per bucket, each
the sum of its DHC variables. The buckets are those of the research, checked
against reference values (issue #88).
"""

from ..core import field_group

FIELDS = field_group("children_by_age", "2020 Census DHC table PCT12, ZCTA", "people", (
    ("male_0", "Male age 0", ("PCT12_003N",)),
    ("male_1", "Male age 1", ("PCT12_004N",)),
    ("male_2", "Male age 2", ("PCT12_005N",)),
    ("male_3", "Male age 3", ("PCT12_006N",)),
    ("male_4", "Male age 4", ("PCT12_007N",)),
    ("male_5", "Male age 5", ("PCT12_008N",)),
    ("male_6", "Male age 6", ("PCT12_009N",)),
    ("male_7", "Male age 7", ("PCT12_010N",)),
    ("male_8", "Male age 8", ("PCT12_011N",)),
    ("male_9", "Male age 9", ("PCT12_012N",)),
    ("male_10", "Male age 10", ("PCT12_013N",)),
    ("male_11", "Male age 11", ("PCT12_014N",)),
    ("male_12", "Male age 12", ("PCT12_015N",)),
    ("male_13", "Male age 13", ("PCT12_016N",)),
    ("male_14", "Male age 14", ("PCT12_017N",)),
    ("male_15", "Male age 15", ("PCT12_018N",)),
    ("male_16", "Male age 16", ("PCT12_019N",)),
    ("male_17", "Male age 17", ("PCT12_020N",)),
    ("male_18", "Male age 18", ("PCT12_021N",)),
    ("male_19", "Male age 19", ("PCT12_022N",)),
    ("male_20", "Male age 20", ("PCT12_023N",)),
    ("female_0", "Female age 0", ("PCT12_107N",)),
    ("female_1", "Female age 1", ("PCT12_108N",)),
    ("female_2", "Female age 2", ("PCT12_109N",)),
    ("female_3", "Female age 3", ("PCT12_110N",)),
    ("female_4", "Female age 4", ("PCT12_111N",)),
    ("female_5", "Female age 5", ("PCT12_112N",)),
    ("female_6", "Female age 6", ("PCT12_113N",)),
    ("female_7", "Female age 7", ("PCT12_114N",)),
    ("female_8", "Female age 8", ("PCT12_115N",)),
    ("female_9", "Female age 9", ("PCT12_116N",)),
    ("female_10", "Female age 10", ("PCT12_117N",)),
    ("female_11", "Female age 11", ("PCT12_118N",)),
    ("female_12", "Female age 12", ("PCT12_119N",)),
    ("female_13", "Female age 13", ("PCT12_120N",)),
    ("female_14", "Female age 14", ("PCT12_121N",)),
    ("female_15", "Female age 15", ("PCT12_122N",)),
    ("female_16", "Female age 16", ("PCT12_123N",)),
    ("female_17", "Female age 17", ("PCT12_124N",)),
    ("female_18", "Female age 18", ("PCT12_125N",)),
    ("female_19", "Female age 19", ("PCT12_126N",)),
    ("female_20", "Female age 20", ("PCT12_127N",)),
))
