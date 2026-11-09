# -*- coding: utf-8 -*-

"""
``housing_occupancy_*``. Claimed by ``census-dhc``.

Housing units by tenure or vacancy; universe: housing units. One column per bucket, each
the sum of its DHC variables. The buckets are those of the research, checked
against reference values (issue #88).
"""

from ..core import field_group

FIELDS = field_group("housing_occupancy", "2020 Census DHC tables H3 and H4, ZCTA", "units", (
    ("owned_mortgage", "Owned with a mortgage or a loan", ("H4_002N",)),
    ("owned_free_clear", "Owned free and clear", ("H4_003N",)),
    ("renter", "Renter occupied", ("H4_004N",)),
    ("vacant", "Vacant", ("H3_003N",)),
))
