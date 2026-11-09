# -*- coding: utf-8 -*-

"""
``head_of_household_by_age_*``. Claimed by ``census-dhc``.

Occupied units by tenure and age of householder; universe: occupied housing units. One column per bucket, each
the sum of its DHC variables. The buckets are those of the research, checked
against reference values (issue #88).
"""

from ..core import field_group

FIELDS = field_group("head_of_household_by_age", "2020 Census DHC table H13, ZCTA", "units", (
    ("owner_15_24", "Owner occupied, householder 15-24", ("H13_003N",)),
    ("owner_25_34", "Owner occupied, householder 25-34", ("H13_004N",)),
    ("owner_35_44", "Owner occupied, householder 35-44", ("H13_005N",)),
    ("owner_45_54", "Owner occupied, householder 45-54", ("H13_006N",)),
    ("owner_55_64", "Owner occupied, householder 55-64", ("H13_007N", "H13_008N")),
    ("owner_65_74", "Owner occupied, householder 65-74", ("H13_009N",)),
    ("owner_75_84", "Owner occupied, householder 75-84", ("H13_010N",)),
    ("owner_85_plus", "Owner occupied, householder 85+", ("H13_011N",)),
    ("renter_15_24", "Renter occupied, householder 15-24", ("H13_013N",)),
    ("renter_25_34", "Renter occupied, householder 25-34", ("H13_014N",)),
    ("renter_35_44", "Renter occupied, householder 35-44", ("H13_015N",)),
    ("renter_45_54", "Renter occupied, householder 45-54", ("H13_016N",)),
    ("renter_55_64", "Renter occupied, householder 55-64", ("H13_017N", "H13_018N")),
    ("renter_65_74", "Renter occupied, householder 65-74", ("H13_019N",)),
    ("renter_75_84", "Renter occupied, householder 75-84", ("H13_020N",)),
    ("renter_85_plus", "Renter occupied, householder 85+", ("H13_021N",)),
))
