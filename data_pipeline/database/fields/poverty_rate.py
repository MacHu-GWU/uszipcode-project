# -*- coding: utf-8 -*-

"""``poverty_rate``. Claimed by ``census-acs5``."""

from ..core import Field, census_int


def _share(row):
    below, everyone = census_int(row["B17001_002E"]), census_int(row["B17001_001E"])
    if below is None or not everyone:
        return None
    return below / everyone


FIELDS = (
    Field(
        name="poverty_rate",
        dtype=float,
        description="Share of the people in the ZCTA (for whom poverty status is determined) below the poverty level, "
                    "0 to 1; latest ACS 5-year table B17001 (B17001_002E / B17001_001E)",
        unit="share",
        extract=_share,
        examples=(
            ({"B17001_002E": "2", "B17001_001E": "8"}, 0.25),
            ({"B17001_002E": "0", "B17001_001E": "0"}, None),
            ({"B17001_002E": "-666666666", "B17001_001E": "100"}, None),
        ),
    ),
)
