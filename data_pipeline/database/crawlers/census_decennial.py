# -*- coding: utf-8 -*-

"""
census-decennial: the population counted by each decennial census since 2000, for
the history table. One Census Data API call per census (under 1 MB each), with the
same free key as ``census-dhc``. A source row is one row of one census, with
``year`` set to the census year; the variable is ``P001001`` in 2000 and 2010
(Summary File 1) and ``P1_001N`` in 2020 (DHC).
"""

import json

from ..core import Crawler, Download, Secret, field_names
from ..fields.history import census_population

CENSUS_KEY = Secret(
    env="CENSUS_API_KEY",
    file="~/.census_key",
    signup_url="https://api.census.gov/data/key_signup.html",
    query_param="key",
)
KEY_COLUMN = "zip code tabulation area"
#: census year -> (dataset, variable)
CENSUSES = {2000: ("sf1", "P001001"), 2010: ("sf1", "P001001"), 2020: ("dhc", "P1_001N")}
URL = "https://api.census.gov/data/{year}/dec/{dataset}?get={variable}&for=zip%20code%20tabulation%20area:*"


def filename(year: int) -> str:
    return "census%d_zcta_population.json" % year


def parse(files):
    for year in CENSUSES:
        with open(files[filename(year)], encoding="utf-8") as fh:
            header, *records = json.load(fh)
        i_key = header.index(KEY_COLUMN)
        for record in records:
            yield record[i_key], dict(zip(header, record), year=year)


CRAWLER = Crawler(
    name="census-decennial",
    fields=field_names(census_population),
    downloads=tuple(Download(filename(year), URL.format(year=year, dataset=dataset, variable=variable),
                             magic=b"[[", secret=CENSUS_KEY) for year, (dataset, variable) in CENSUSES.items()),
    parse=parse,
    description="Census 2000, 2010 and 2020 -> population by census year",
    history=True,
)
