# -*- coding: utf-8 -*-

"""
``radius_in_miles``. Derived: computed by ``build`` from the four ``bounds_*`` Fields, claimed by no crawler.

It is half the diagonal of the bounding box: the radius of the circle around the middle of the box
that reaches its corners, so the whole ZCTA lies inside that circle. The 2.x column of this name has
no documented definition. Its values are whole miles (below one mile, multiples of 300 feet), and
for 81% of the ZIPs that have one, half the diagonal of the 2.x box is within one mile or 25% of it.
The radius of a circle with the area of the ZCTA is within that distance for 18%.
"""

import math

from ..core import EARTH_RADIUS_MILES, Field, half_diagonal_miles

FIELDS = (
    Field(
        name="radius_in_miles",
        dtype=float,
        simple=True,
        description=("Half the diagonal of the ZCTA bounding box: half the great-circle distance between "
                     "its south-west and north-east corners"),
        unit="miles",
        inputs=("bounds_west", "bounds_east", "bounds_north", "bounds_south"),
        extract=half_diagonal_miles("bounds_west", "bounds_east", "bounds_north", "bounds_south"),
        examples=(
            # a box that spans half the equator: its diagonal is half the circumference
            ({"bounds_west": -90.0, "bounds_east": 90.0, "bounds_north": 0.0, "bounds_south": 0.0},
             EARTH_RADIUS_MILES * math.pi / 2),
            ({"bounds_west": -77.0, "bounds_east": -77.0, "bounds_north": 38.0, "bounds_south": 38.0}, 0.0),
            ({"bounds_west": None, "bounds_east": None, "bounds_north": None, "bounds_south": None}, None),
        ),
    ),
)
