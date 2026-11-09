# -*- coding: utf-8 -*-

"""
``population_by_gender_*``. Claimed by ``census-dhc``.

Population by sex; universe: total population. One column per bucket, each
the sum of its DHC variables. The buckets are those of the research, checked
against reference values (issue #88).
"""

from ..core import field_group

FIELDS = field_group("population_by_gender", "2020 Census DHC table P12, ZCTA", "people", (
    ("male", "Male", ("P12_002N",)),
    ("female", "Female", ("P12_026N",)),
))
