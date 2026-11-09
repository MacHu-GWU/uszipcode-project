# -*- coding: utf-8 -*-

"""
zcta-geometry: where a ZCTA is. Three downloads, no key:

- Census TIGER/Line 2025 ZCTA shapefile (about 529 MB), the full-resolution
  boundaries of the 2020 ZCTAs. Only two things are read from it: the box that each
  shape record carries (``Xmin``, ``Ymin``, ``Xmax``, ``Ymax``, as the shapefile
  specification names them) and the internal point (``INTPTLAT20``, ``INTPTLON20``).
- Census cartographic boundary file 2020 ZCTA at 1:500,000 (about 67 MB): the same
  ZCTAs, generalized by the Census Bureau for maps. Column ``geometry`` is the shape
  as GeoJSON text.
- BTS NTAD Time Zones (about 9 MB of GeoJSON, one polygon per standard-time zone):
  ``zone`` and ``utc`` of the zone that contains the internal point.

A time zone needs a point, and the point is in a Census file. A second crawler
could not download that file again (rule C8), so the three files are one crawler.

The shapefiles are read by the small reader below (standard library only): a
``.shp`` file is a 100-byte header and one record per shape; a ``.dbf`` file holds
the attributes, one record per shape, in the same order.
"""

import array
import json
import math
import os
import struct
import sys
import zipfile

from ..core import Crawler, Download, field_names
from ..fields import bounds, polygon, timezone

TIGER_URL = "https://www2.census.gov/geo/tiger/TIGER2025/ZCTA520/tl_2025_us_zcta520.zip"
TIGER_FILENAME = "tl_2025_us_zcta520.zip"
CB_URL = "https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_us_zcta520_500k.zip"
CB_FILENAME = "cb_2020_us_zcta520_500k.zip"
BTS_URL = ("https://services.arcgis.com/xOi1kZaI0eWDREZv/ArcGIS/rest/services/NTAD_Time_Zones/FeatureServer/0/"
           "query?where=1%3D1&outFields=zone,utc&outSR=4326&f=geojson")
BTS_FILENAME = "ntad_time_zones.geojson"

KEY_COLUMN = "ZCTA5CE20"
POINT_COLUMNS = ("INTPTLAT20", "INTPTLON20")
BOX_COLUMNS = ("Xmin", "Ymin", "Xmax", "Ymax")
DECIMALS = 6  # of the GeoJSON coordinates: about 0.1 m
BAND = 0.01  # degrees of latitude per bucket of zone edges


# ------------------------------------------------------------------------------------------ shapefile
def _member(z: zipfile.ZipFile, extension: str) -> str:
    names = [n for n in z.namelist() if os.path.splitext(n)[1].lower() == extension]
    if len(names) != 1:
        raise ValueError("expected one %s file in %s, found %s" % (extension, z.filename, names))
    return names[0]


def _read(fh, size: int) -> bytes:
    data = fh.read(size)
    if len(data) != size:
        raise ValueError("the shapefile ends in the middle of a record")
    return data


def read_dbf(data: bytes, columns) -> list:
    """The ``columns`` of every record of a dBase file, as text."""
    count, header_size, record_size = struct.unpack("<IHH", data[4:12])
    where, offset, pos = {}, 1, 32  # byte 0 of a record is its deletion flag
    while data[pos] != 0x0D:
        name = data[pos:pos + 11].split(b"\x00")[0].decode("ascii")
        where[name], offset, pos = (offset, data[pos + 16]), offset + data[pos + 16], pos + 32
    missing = [c for c in columns if c not in where]
    if missing:
        raise ValueError("the .dbf file has no column %s; it has %s" % (", ".join(missing), ", ".join(where)))
    spans = [(c,) + where[c] for c in columns]
    rows = []
    for i in range(count):
        record = data[header_size + i * record_size:header_size + (i + 1) * record_size]
        rows.append({c: record[o:o + n].decode("utf-8").strip() for c, o, n in spans})
    return rows


def shp_records(fh):
    """The content of each record of a ``.shp`` stream: shape type, box, parts, points."""
    header = _read(fh, 100)
    if struct.unpack(">i", header[:4])[0] != 9994:
        raise ValueError("not a shapefile (file code %r)" % header[:4])
    while True:
        head = fh.read(8)
        if not head:
            return
        if len(head) != 8:
            raise ValueError("the shapefile ends in the middle of a record header")
        yield _read(fh, struct.unpack(">i", head[4:8])[0] * 2)  # the length is in 16-bit words


def _shape_type(content: bytes) -> int:
    shape_type = struct.unpack("<i", content[:4])[0]
    if shape_type not in (0, 5, 15, 25):  # null shape, or polygon (plain, Z, M)
        raise ValueError("shape type %d is not a polygon" % shape_type)
    return shape_type


def rings(content: bytes) -> list:
    """The rings of a polygon record, each a list of (x, y)."""
    n_parts, n_points = struct.unpack("<2i", content[36:44])
    starts = struct.unpack("<%di" % n_parts, content[44:44 + 4 * n_parts]) + (n_points,)
    xy = array.array("d")
    xy.frombytes(content[44 + 4 * n_parts:44 + 4 * n_parts + 16 * n_points])
    if sys.byteorder == "big":
        xy.byteswap()
    return [list(zip(xy[2 * a:2 * b:2], xy[2 * a + 1:2 * b:2])) for a, b in zip(starts, starts[1:])]


def box(content: bytes) -> dict:
    """``Xmin``, ``Ymin``, ``Xmax``, ``Ymax`` of a record. A shape across the 180th meridian (wider than
    180 degrees as stored) gets its real west and east edges from its points, so ``Xmin`` > ``Xmax``."""
    x_min, y_min, x_max, y_max = struct.unpack("<4d", content[4:36])
    if x_max - x_min > 180:
        xs = [x + 360 if x < 0 else x for ring in rings(content) for x, _ in ring]
        x_min, x_max = min(xs), max(xs)
        x_min, x_max = (x_min - 360 if x_min > 180 else x_min), (x_max - 360 if x_max > 180 else x_max)
    return dict(zip(BOX_COLUMNS, (x_min, y_min, x_max, y_max)))


# ------------------------------------------------------------------------------------------- geometry
def _area2(ring) -> float:
    """Twice the signed area (positive when counter-clockwise, with y up)."""
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:]))


def _inside(x: float, y: float, ring) -> bool:
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def _extent(ring):
    xs, ys = [p[0] for p in ring], [p[1] for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


def _covers(outer, inner) -> bool:
    return outer[0] <= inner[0] and outer[1] <= inner[1] and inner[2] <= outer[2] and inner[3] <= outer[3]


def to_geojson(content: bytes) -> str:
    """
    A polygon record as GeoJSON text. In a shapefile, outer rings run clockwise and holes
    counter-clockwise, with nothing saying which outer ring a hole belongs to: a hole
    goes to the smallest outer ring that contains it. RFC 7946 wants the opposite
    orientation, so every ring is reversed.
    """
    shells, holes = [], []
    for ring in rings(content):
        if len(ring) >= 4:
            (shells if _area2(ring) < 0 else holes).append(ring)
    polygons = [[ring] for ring in shells]
    extents = [_extent(ring) for ring in shells]
    sizes = [-_area2(ring) for ring in shells]
    for hole in holes:
        extent = _extent(hole)
        around = [i for i in range(len(shells)) if _covers(extents[i], extent)]
        owners = [i for i in around if _inside(hole[0][0], hole[0][1], shells[i])] or around
        if owners:
            polygons[min(owners, key=sizes.__getitem__)].append(hole)
        else:  # not inside any outer ring: an outer ring stored the wrong way round
            polygons.append([hole[::-1]])
    coordinates = [[[[round(x, DECIMALS), round(y, DECIMALS)] for x, y in reversed(ring)] for ring in rings_]
                   for rings_ in polygons]
    if len(coordinates) == 1:
        geometry = {"type": "Polygon", "coordinates": coordinates[0]}
    else:
        geometry = {"type": "MultiPolygon", "coordinates": coordinates}
    return json.dumps(geometry, separators=(",", ":"))


class TimeZones:
    """The BTS zone polygons, with their edges in bands of latitude so that a lookup reads few edges."""

    def __init__(self, features):
        self.zones = []
        for feature in features:
            geometry = feature["geometry"]
            parts = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
            edges, extent = {}, None
            for ring in (ring for part in parts for ring in part):
                ring = [tuple(p[:2]) for p in ring]
                if ring[0] != ring[-1]:
                    ring.append(ring[0])
                e = _extent(ring)
                extent = e if extent is None else (min(extent[0], e[0]), min(extent[1], e[1]),
                                                   max(extent[2], e[2]), max(extent[3], e[3]))
                for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
                    if y1 != y2:  # a horizontal edge never crosses a horizontal ray
                        for band in range(math.floor(min(y1, y2) / BAND), math.floor(max(y1, y2) / BAND) + 1):
                            edges.setdefault(band, []).append((x1, y1, x2, y2))
            self.zones.append((dict(feature["properties"]), extent, edges))

    def find(self, x: float, y: float) -> dict:
        """The properties of the first zone that contains the point (even-odd rule), else {}."""
        band = math.floor(y / BAND)
        for properties, (x_min, y_min, x_max, y_max), edges in self.zones:
            if x_min <= x <= x_max and y_min <= y <= y_max:
                inside = False
                for x1, y1, x2, y2 in edges.get(band, ()):
                    if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                        inside = not inside
                if inside:
                    return properties
        return {}


# ---------------------------------------------------------------------------------------------- parse
def _tiger(path):
    """(ZCTA, {internal point, box}) for every record of the TIGER/Line file."""
    with zipfile.ZipFile(path) as z:
        attributes = read_dbf(z.read(_member(z, ".dbf")), (KEY_COLUMN,) + POINT_COLUMNS)
        with z.open(_member(z, ".shp")) as fh:
            for i, content in enumerate(shp_records(fh)):
                row = attributes[i]
                row.update(box(content) if _shape_type(content) else dict.fromkeys(BOX_COLUMNS))
                yield row[KEY_COLUMN], row


def _cartographic(path) -> dict:
    """ZCTA -> GeoJSON text, from the cartographic boundary file."""
    with zipfile.ZipFile(path) as z:
        attributes = read_dbf(z.read(_member(z, ".dbf")), (KEY_COLUMN,))
        with z.open(_member(z, ".shp")) as fh:
            return {attributes[i][KEY_COLUMN]: to_geojson(content) if _shape_type(content) else None
                    for i, content in enumerate(shp_records(fh))}


def parse(files):
    with open(files[BTS_FILENAME], encoding="utf-8") as fh:
        zones = TimeZones(json.load(fh)["features"])
    shapes = _cartographic(files[CB_FILENAME])
    empty = dict.fromkeys(POINT_COLUMNS + BOX_COLUMNS + ("zone", "utc", "geometry"))
    for zcta, row in _tiger(files[TIGER_FILENAME]):
        lat, lng = (row[c] for c in POINT_COLUMNS)
        zone = zones.find(float(lng), float(lat)) if lat and lng else {}
        yield zcta, dict(empty, **row, zone=zone.get("zone"), utc=zone.get("utc"), geometry=shapes.pop(zcta, None))
    for zcta, geometry in shapes.items():  # in the cartographic file only
        yield zcta, dict(empty, **{KEY_COLUMN: zcta, "geometry": geometry})


CRAWLER = Crawler(
    name="zcta-geometry",
    fields=field_names(bounds, timezone, polygon),
    downloads=(
        Download(TIGER_FILENAME, TIGER_URL, magic=b"PK\x03\x04"),
        Download(CB_FILENAME, CB_URL, magic=b"PK\x03\x04"),
        Download(BTS_FILENAME, BTS_URL, magic=b"{"),
    ),
    parse=parse,
    description="Census TIGER/Line and cartographic ZCTA boundaries, BTS time zones -> bounding box, time zone, polygon",
)
