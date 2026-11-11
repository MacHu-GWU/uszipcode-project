# -*- coding: utf-8 -*-

"""``population_density``. Derived: computed by ``build`` from two earlier Fields, claimed by no crawler."""

from ..core import Field, ratio

FIELDS = (
    Field(
        name="population_density",
        dtype=float,
        description="People per square mile of land in the ZCTA: population / land_area_in_sqmi; NULL where the land area is 0",
        unit="people per sq mi",
        inputs=("population", "land_area_in_sqmi"),
        extract=ratio("population", "land_area_in_sqmi"),
        examples=(
            ({"population": 14945, "land_area_in_sqmi": 0.732}, 14945 / 0.732),
            ({"population": 25, "land_area_in_sqmi": 0.0}, None),
            ({"population": None, "land_area_in_sqmi": 1.5}, None),
        ),
    ),
)
