# -*- coding: utf-8 -*-

"""
``means_of_transportation_to_work_*``. Claimed by ``census-acs5``.

Workers 16+ by means of transportation to work; universe: workers 16+. One column per bucket,
each the sum of its ACS variables. The buckets are those of the research, checked against
reference values (issue #88).

Stands for the 2.x field(s) ``means_of_transportation_to_work_for_workers_16_and_over``.
"""

from ..core import census_int, field_group

FIELDS = field_group("means_of_transportation_to_work", "latest ACS 5-year table B08301, ZCTA", "workers", (
    ("car", "Car, truck, or van", ("B08301_002E",)),
    ("public_transit", "Public transportation (excl. taxi)", ("B08301_010E",)),
    ("taxi", "Taxicab", ("B08301_016E",)),
    ("motorcycle", "Motorcycle", ("B08301_017E",)),
    ("bike_walk_other", "Bicycle, walked, or other", ("B08301_018E", "B08301_019E", "B08301_020E")),
    ("work_from_home", "Worked from home", ("B08301_021E",)),
), convert=census_int)
