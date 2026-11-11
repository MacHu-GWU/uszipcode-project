# -*- coding: utf-8 -*-

"""
``families_vs_singles_*``. Claimed by ``census-dhc``.

Households by type (native P16 categories); universe: households. One column per bucket, each
the sum of its DHC variables. The buckets are those of the research, checked
against reference values (issue #88).
"""

from ..core import field_group

FIELDS = field_group("families_vs_singles", "2020 Census DHC table P16, ZCTA", "households", (
    ("married_couple_family", "Married couple family", ("P16_003N",)),
    ("other_family_male", "Other family, male householder, no spouse", ("P16_005N",)),
    ("other_family_female", "Other family, female householder, no spouse", ("P16_006N",)),
    ("living_alone", "Nonfamily, householder living alone", ("P16_008N",)),
    ("not_living_alone", "Nonfamily, householder not living alone", ("P16_009N",)),
))
