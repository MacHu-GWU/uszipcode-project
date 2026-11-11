# -*- coding: utf-8 -*-

"""
``vacancy_reason_*``. Claimed by ``census-dhc``.

Vacant housing units by status; universe: vacant housing units. One column per bucket, each
the sum of its DHC variables. The buckets are those of the research, checked
against reference values (issue #88).
"""

from ..core import field_group

FIELDS = field_group("vacancy_reason", "2020 Census DHC table H5, ZCTA", "units", (
    ("for_rent", "For rent", ("H5_002N",)),
    ("rented_unoccupied", "Rented, not occupied", ("H5_003N",)),
    ("for_sale", "For sale only", ("H5_004N",)),
    ("sold_unoccupied", "Sold, not occupied", ("H5_005N",)),
    ("seasonal", "For seasonal, recreational, or occasional use", ("H5_006N",)),
    ("migrant_workers", "For migrant workers", ("H5_007N",)),
    ("other", "Other vacant", ("H5_008N",)),
))
