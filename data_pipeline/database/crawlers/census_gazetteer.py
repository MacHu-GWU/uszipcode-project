# -*- coding: utf-8 -*-

"""
census-gazetteer: Census Gazetteer ZCTA file -> lat, lng, land_area_in_sqmi.

One download (about 1 MB, no key). The zip holds one pipe-delimited text file with
the header ``GEOID|GEOIDFQ|ALAND|AWATER|ALAND_SQMI|AWATER_SQMI|INTPTLAT|INTPTLONG``.
"""

import csv
import io
import zipfile

from ..core import Crawler, Download, parse_float

URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
    "2025_Gazetteer/2025_Gaz_zcta_national.zip"
)
FILENAME = "2025_Gaz_zcta_national.zip"
COLUMNS = {"lat": "INTPTLAT", "lng": "INTPTLONG", "land_area_in_sqmi": "ALAND_SQMI"}


def parse(files):
    with zipfile.ZipFile(files[FILENAME]) as z:
        members = [n for n in z.namelist() if n.lower().endswith(".txt")]
        if len(members) != 1:
            raise ValueError("expected one .txt file in %s, found %s" % (FILENAME, members))
        text = z.read(members[0]).decode("utf-8")
    reader = csv.reader(io.StringIO(text), delimiter="|")
    header = [h.strip() for h in next(reader)]
    missing = [c for c in ["GEOID"] + list(COLUMNS.values()) if c not in header]
    if missing:
        raise ValueError("Gazetteer header has no column %s: %s" % (", ".join(missing), "|".join(header)))
    i_geoid = header.index("GEOID")
    index = {field: header.index(column) for field, column in COLUMNS.items()}
    for row in reader:
        if not row:
            continue
        row = [cell.strip() for cell in row]
        yield row[i_geoid], {field: parse_float(row[i]) for field, i in index.items()}


CRAWLER = Crawler(
    name="census-gazetteer",
    fields=("lat", "lng", "land_area_in_sqmi"),
    downloads=(Download(FILENAME, URL, magic=b"PK\x03\x04"),),
    parse=parse,
    description="Census Gazetteer 2025 ZCTA -> lat, lng, land_area_in_sqmi",
)
