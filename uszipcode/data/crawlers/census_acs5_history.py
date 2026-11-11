# -*- coding: utf-8 -*-

"""
census-acs5-history: a few ACS 5-year estimates for every vintage from 2011, for the
history table. One Census Data API call per vintage (about 2 MB each), with the same
free key as ``census-dhc``. The API has no ZCTA data in the 5-year files before 2011.
A source row is one row of one vintage, with ``year`` set to that vintage.

``LAST_YEAR`` should follow ``census_acs5.YEAR``.
"""

import json

from ..core import Crawler, Download, Secret, field_names
from ..fields.history import acs_population, median_household_income, median_home_value, median_rent

FIRST_YEAR, LAST_YEAR = 2011, 2024
URL = "https://api.census.gov/data/{year}/acs/acs5?get={variables}&for=zip%20code%20tabulation%20area:*"
CENSUS_KEY = Secret(
    env="CENSUS_API_KEY",
    file="~/.census_key",
    signup_url="https://api.census.gov/data/key_signup.html",
    query_param="key",
)
KEY_COLUMN = "zip code tabulation area"
VARIABLES = ("B01003_001E", "B01003_001M", "B19013_001E", "B19013_001M",
             "B25077_001E", "B25077_001M", "B25064_001E", "B25064_001M")
YEARS = tuple(range(FIRST_YEAR, LAST_YEAR + 1))


def filename(year: int) -> str:
    return "acs5_%d_zcta_history.json" % year


def parse(files):
    for year in YEARS:
        with open(files[filename(year)], encoding="utf-8") as fh:
            header, *records = json.load(fh)
        i_key = header.index(KEY_COLUMN)
        for record in records:
            yield record[i_key], dict(zip(header, record), year=year)


CRAWLER = Crawler(
    name="census-acs5-history",
    fields=field_names(acs_population, median_household_income, median_home_value, median_rent),
    downloads=tuple(Download(filename(year), URL.format(year=year, variables=",".join(VARIABLES)),
                             magic=b"[[", secret=CENSUS_KEY) for year in YEARS),
    parse=parse,
    description="ACS 5-year %d-%d -> population, median income, home value and rent by year" % (FIRST_YEAR, LAST_YEAR),
    history=True,
)
