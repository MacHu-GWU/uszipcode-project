# -*- coding: utf-8 -*-

"""
``households_with_kids_*``. Claimed by ``census-dhc``.

Households by presence of people under 18; universe: households. One column per bucket, each
the sum of its DHC variables. The buckets are those of the research, checked
against reference values (issue #88).
"""

from ..core import field_group

FIELDS = field_group("households_with_kids", "2020 Census DHC table P21, ZCTA", "households", (
    ("with_kids", "With one or more people under 18", ("P21_002N",)),
    ("no_kids", "With no people under 18", ("P21_005N",)),
))
