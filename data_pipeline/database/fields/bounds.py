# -*- coding: utf-8 -*-

"""
``bounds_west``, ``bounds_east``, ``bounds_north``, ``bounds_south``: the bounding box
of the ZCTA. Claimed by ``zcta-geometry``.

The box is the one each record of the TIGER/Line shapefile carries (``Xmin``, ``Xmax``,
``Ymin``, ``Ymax`` in the shapefile specification), so it covers the full-resolution
boundary, water included. A ZCTA that crosses the 180th meridian would have
``bounds_west`` > ``bounds_east`` (none does in the 2020 ZCTAs).
"""

from ..core import Field, column, parse_float

SOURCE = "Census TIGER/Line 2025 ZCTA, full-resolution boundary"

FIELDS = (
    Field(
        name="bounds_west",
        dtype=float,
        description="West edge (smallest longitude) of the ZCTA bounding box; %s (Xmin)" % SOURCE,
        unit="degrees",
        extract=column("Xmin", parse_float),
        examples=(({"Xmin": -77.064696}, -77.064696), ({"Xmin": None}, None)),
    ),
    Field(
        name="bounds_east",
        dtype=float,
        description="East edge (largest longitude) of the ZCTA bounding box; %s (Xmax)" % SOURCE,
        unit="degrees",
        extract=column("Xmax", parse_float),
        examples=(({"Xmax": -77.04624}, -77.04624), ({"Xmax": None}, None)),
    ),
    Field(
        name="bounds_north",
        dtype=float,
        description="North edge (largest latitude) of the ZCTA bounding box; %s (Ymax)" % SOURCE,
        unit="degrees",
        extract=column("Ymax", parse_float),
        examples=(({"Ymax": 38.910414}, 38.910414), ({"Ymax": None}, None)),
    ),
    Field(
        name="bounds_south",
        dtype=float,
        description="South edge (smallest latitude) of the ZCTA bounding box; %s (Ymin)" % SOURCE,
        unit="degrees",
        extract=column("Ymin", parse_float),
        examples=(({"Ymin": 38.87131}, 38.87131), ({"Ymin": None}, None)),
    ),
)
