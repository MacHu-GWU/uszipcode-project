# -*- coding: utf-8 -*-

"""
``timezone``. Claimed by ``zip-basics``.

A zone needs a point, and the best point a ZIP has decides: the internal point of
its ZCTA; without a ZCTA (PO box, unique and other ZIPs), the internal point of its
main county (the HUD county, else the county 2.x names); without a county, its
state, when all counties of the state are in one zone. The county and state steps
can be wrong where a county spans two zones.
"""

from ..core import Field, first_value

FIELDS = (
    Field(
        name="timezone",
        dtype=str,
        simple=True,
        description=("Standard-time zone, e.g. Eastern (BTS NTAD Time Zones, property zone): the zone that contains "
                     "the ZCTA internal point; for a ZIP without a ZCTA, the zone at the internal point of its main "
                     "county, else the zone of its state when the whole state is in one zone. It does not say "
                     "whether the place observes daylight saving time"),
        unit="zone name",
        extract=first_value("zcta_zone", "county_zone", "v2_county_zone", "hud_state_zone", "zbp_state_zone",
                            "v2_state_zone"),
        examples=(
            ({"zcta_zone": "Eastern", "county_zone": "Central", "hud_state_zone": "Central"}, "Eastern"),
            ({"county_zone": "Central", "v2_county_zone": "Mountain", "hud_state_zone": "Eastern"}, "Central"),
            ({"v2_county_zone": "Mountain", "zbp_state_zone": "Central"}, "Mountain"),
            ({"hud_state_zone": "Eastern", "zbp_state_zone": "Central", "v2_state_zone": "Pacific"}, "Eastern"),
            ({"v2_state_zone": "Pacific"}, "Pacific"),
            ({}, None),
        ),
    ),
)
