# -*- coding: utf-8 -*-

"""
``population_by_age_*``. Claimed by ``census-dhc``.

Population by sex and 5-year age band (adjacent P12 bands merged); universe: total population. One column per bucket, each
the sum of its DHC variables. The buckets are those of the research, checked
against reference values (issue #88).
"""

from ..core import field_group

FIELDS = field_group("population_by_age", "2020 Census DHC table P12, ZCTA", "people", (
    ("male_0_4", "Male 0-4", ("P12_003N",)),
    ("male_5_9", "Male 5-9", ("P12_004N",)),
    ("male_10_14", "Male 10-14", ("P12_005N",)),
    ("male_15_19", "Male 15-19", ("P12_006N", "P12_007N")),
    ("male_20_24", "Male 20-24", ("P12_008N", "P12_009N", "P12_010N")),
    ("male_25_29", "Male 25-29", ("P12_011N",)),
    ("male_30_34", "Male 30-34", ("P12_012N",)),
    ("male_35_39", "Male 35-39", ("P12_013N",)),
    ("male_40_44", "Male 40-44", ("P12_014N",)),
    ("male_45_49", "Male 45-49", ("P12_015N",)),
    ("male_50_54", "Male 50-54", ("P12_016N",)),
    ("male_55_59", "Male 55-59", ("P12_017N",)),
    ("male_60_64", "Male 60-64", ("P12_018N", "P12_019N")),
    ("male_65_69", "Male 65-69", ("P12_020N", "P12_021N")),
    ("male_70_74", "Male 70-74", ("P12_022N",)),
    ("male_75_79", "Male 75-79", ("P12_023N",)),
    ("male_80_84", "Male 80-84", ("P12_024N",)),
    ("male_85_plus", "Male 85+", ("P12_025N",)),
    ("female_0_4", "Female 0-4", ("P12_027N",)),
    ("female_5_9", "Female 5-9", ("P12_028N",)),
    ("female_10_14", "Female 10-14", ("P12_029N",)),
    ("female_15_19", "Female 15-19", ("P12_030N", "P12_031N")),
    ("female_20_24", "Female 20-24", ("P12_032N", "P12_033N", "P12_034N")),
    ("female_25_29", "Female 25-29", ("P12_035N",)),
    ("female_30_34", "Female 30-34", ("P12_036N",)),
    ("female_35_39", "Female 35-39", ("P12_037N",)),
    ("female_40_44", "Female 40-44", ("P12_038N",)),
    ("female_45_49", "Female 45-49", ("P12_039N",)),
    ("female_50_54", "Female 50-54", ("P12_040N",)),
    ("female_55_59", "Female 55-59", ("P12_041N",)),
    ("female_60_64", "Female 60-64", ("P12_042N", "P12_043N")),
    ("female_65_69", "Female 65-69", ("P12_044N", "P12_045N")),
    ("female_70_74", "Female 70-74", ("P12_046N",)),
    ("female_75_79", "Female 75-79", ("P12_047N",)),
    ("female_80_84", "Female 80-84", ("P12_048N",)),
    ("female_85_plus", "Female 85+", ("P12_049N",)),
))
