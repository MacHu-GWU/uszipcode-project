# -*- coding: utf-8 -*-

"""``timezone``. Claimed by ``zcta-geometry``."""

from ..core import Field, column

FIELDS = (
    Field(
        name="timezone",
        dtype=str,
        simple=True,
        description=("Standard-time zone that contains the ZCTA internal point, e.g. Eastern (BTS NTAD Time Zones, "
                     "property zone). It does not say whether the place observes daylight saving time"),
        unit="zone name",
        extract=column("zone"),
        examples=(({"zone": "Eastern", "utc": "-05:00"}, "Eastern"), ({"zone": None, "utc": None}, None)),
    ),
)
