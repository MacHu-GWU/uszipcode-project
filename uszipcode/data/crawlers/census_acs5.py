# -*- coding: utf-8 -*-

"""
census-acs5: American Community Survey 5-year estimates, latest vintage.

``YEAR`` is the last year of the 5-year window (2024 means 2020-2024); dollar
values are in dollars of that year. The Census Data API returns every ZCTA in one
call but at most 50 variables per call, so the variables are requested in a few
calls. It needs the same free key as ``census-dhc``. A source row has one column per
variable, keyed by ``zip code tabulation area``. The API writes "not available" as
negative codes (for example -666666666); the Fields read them as NULL.

To claim another variable, add it to ``REQUESTS`` and the Field's module to ``fields``.
"""

import json

from ..core import Crawler, Download, field_names
from ..keys import CENSUS_KEY
from ..fields import (
    median_age, median_home_value, owner_occupied_home_values, year_housing_was_built,
    median_rent, rental_properties_by_number_of_rooms, monthly_rent_including_utilities,
    median_household_income, household_income, annual_individual_earnings, employment_status, poverty_rate,
    means_of_transportation_to_work, travel_time_to_work_in_minutes,
    educational_attainment, school_enrollment_age_3_to_17,
)

YEAR = 2024
URL = "https://api.census.gov/data/{year}/acs/acs5?get={variables}&for=zip%20code%20tabulation%20area:*"
KEY_COLUMN = "zip code tabulation area"


def _numbered(table: str, *ranges):
    return tuple("%s_%03dE" % (table, i) for first, last in ranges for i in range(first, last + 1))


#: (part of the cached file name, variables); at most 50 variables per request
REQUESTS = (
    ("medians_income",
     ("B01002_001E", "B01002_001M", "B25077_001E", "B25077_001M", "B19013_001E", "B19013_001M",
      "B25064_001E", "B25064_001M", "B17001_001E", "B17001_002E")
     + _numbered("B19001", (2, 17)) + _numbered("B25034", (2, 11)) + _numbered("B25042", (10, 15))),
    ("commute_work",
     _numbered("B08301", (2, 2), (10, 10), (16, 21)) + _numbered("B08303", (2, 13))
     + _numbered("B20005", (4, 5), (27, 28), (51, 52), (74, 75))),
    ("B20001", _numbered("B20001", (3, 22), (24, 43))),
    ("B25068", _numbered("B25068", (4, 10), (13, 19), (22, 28), (31, 37))),
    ("B25075", _numbered("B25075", (2, 27))),
    ("B14003_B15003",
     _numbered("B14003", (4, 7), (13, 16), (22, 25), (32, 35), (41, 44), (50, 53)) + _numbered("B15003", (2, 25))),
)
VARIABLES = tuple(v for _, variables in REQUESTS for v in variables)


def filename(year: int, part: str) -> str:
    return "acs5_%d_zcta_%s.json" % (year, part)


def parse_for(year: int):
    def parse(files):
        rows = {}
        for part, _ in REQUESTS:
            with open(files[filename(year, part)], encoding="utf-8") as fh:
                header, *records = json.load(fh)
            i_key = header.index(KEY_COLUMN)
            for record in records:
                rows.setdefault(record[i_key], {}).update(zip(header, record))
        return iter(rows.items())
    return parse


def crawler_for(year: int) -> Crawler:
    """The crawler for one ACS vintage (``CRAWLER`` is the latest)."""
    return Crawler(
        name="census-acs5",
        fields=field_names(
            median_age, median_home_value, owner_occupied_home_values, year_housing_was_built,
            median_rent, rental_properties_by_number_of_rooms, monthly_rent_including_utilities,
            median_household_income, household_income, annual_individual_earnings, employment_status, poverty_rate,
            means_of_transportation_to_work, travel_time_to_work_in_minutes,
            educational_attainment, school_enrollment_age_3_to_17,
        ),
        downloads=tuple(
            Download(filename(year, part), URL.format(year=year, variables=",".join(variables)),
                     magic=b"[[", secret=CENSUS_KEY)
            for part, variables in REQUESTS
        ),
        parse=parse_for(year),
        description="ACS %d-%d 5-year -> medians, poverty rate and 11 distributions" % (year - 4, year),
    )


CRAWLER = crawler_for(YEAR)
