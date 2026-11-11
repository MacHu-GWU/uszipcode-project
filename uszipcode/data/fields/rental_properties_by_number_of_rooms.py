# -*- coding: utf-8 -*-

"""
``rental_properties_by_number_of_rooms_*``. Claimed by ``census-acs5``.

Renter-occupied units by number of bedrooms; universe: renter-occupied housing units. One column
per bucket, each the sum of its ACS variables. The buckets are those of the research, checked
against reference values (issue #88).
"""

from ..core import census_int, field_group

FIELDS = field_group("rental_properties_by_number_of_rooms", "latest ACS 5-year table B25042, ZCTA", "units", (
    ("studio", "No bedroom (studio)", ("B25042_010E",)),
    ("1br", "1 bedroom", ("B25042_011E",)),
    ("2br", "2 bedrooms", ("B25042_012E",)),
    ("3br_plus", "3 or more bedrooms", ("B25042_013E", "B25042_014E", "B25042_015E")),
), convert=census_int)
