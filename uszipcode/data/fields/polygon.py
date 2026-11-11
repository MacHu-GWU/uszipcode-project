# -*- coding: utf-8 -*-

"""
``polygon``. Claimed by ``zcta-geometry``.

The boundary as GeoJSON text (RFC 7946: longitude first, outer rings counter-clockwise,
6 decimals). It comes from the Census cartographic boundary file, which the Census
Bureau generalized for maps at 1:500,000, so no simplification is done here. It is the
last column of the catalog because it is by far the longest, and the database stores it
compressed (``compressed=True``; see ``core.Field``).
"""

from ..core import Field, column

SQUARE = '{"type":"Polygon","coordinates":[[[-77.0,38.9],[-76.9,38.9],[-76.9,39.0],[-77.0,39.0],[-77.0,38.9]]]}'

FIELDS = (
    Field(
        name="polygon",
        dtype=str,
        description=("Boundary of the ZCTA as a GeoJSON Polygon or MultiPolygon (longitude, latitude); Census "
                     "cartographic boundary file 2020 ZCTA, generalized at 1:500,000"),
        unit="GeoJSON",
        extract=column("geometry"),
        compressed=True,
        examples=(({"geometry": SQUARE}, SQUARE), ({"geometry": None}, None)),
    ),
)
