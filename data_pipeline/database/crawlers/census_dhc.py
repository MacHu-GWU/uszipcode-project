# -*- coding: utf-8 -*-

"""
census-dhc: 2020 Census Demographic and Housing Characteristics -> population, housing_units.

One Census Data API call returns every ZCTA (about 0.8 MB). It needs a free API key,
read from ``$CENSUS_API_KEY`` or ``~/.census_key``; the framework adds it to the
request and never writes it anywhere.
"""

import json

from ..core import Crawler, Download, Secret, parse_int

URL = (
    "https://api.census.gov/data/2020/dec/dhc?get=P1_001N,H1_001N"
    "&for=zip%20code%20tabulation%20area:*"
)
FILENAME = "dhc2020_zcta_P1_H1.json"
CENSUS_KEY = Secret(
    env="CENSUS_API_KEY",
    file="~/.census_key",
    signup_url="https://api.census.gov/data/key_signup.html",
    query_param="key",
)
COLUMNS = {"population": "P1_001N", "housing_units": "H1_001N"}
KEY_COLUMN = "zip code tabulation area"


def parse(files):
    with open(files[FILENAME], encoding="utf-8") as fh:
        header, *rows = json.load(fh)
    i_key = header.index(KEY_COLUMN)
    index = {field: header.index(column) for field, column in COLUMNS.items()}
    for row in rows:
        yield row[i_key], {field: parse_int(row[i]) for field, i in index.items()}


CRAWLER = Crawler(
    name="census-dhc",
    fields=("population", "housing_units"),
    downloads=(Download(FILENAME, URL, magic=b"[[", secret=CENSUS_KEY),),
    parse=parse,
    description="2020 Census DHC -> population, housing_units",
)
