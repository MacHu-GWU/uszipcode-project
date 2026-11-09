# -*- coding: utf-8 -*-

"""
census-dhc: 2020 Census Demographic and Housing Characteristics.

The Census Data API returns every ZCTA in one call but at most 50 variables per
call, so the variables are requested in a few calls (about 11 MB in all). It needs a
free API key, read from ``$CENSUS_API_KEY`` or ``~/.census_key``; the framework adds
it to the request and never writes it anywhere. A source row has one column per
variable, keyed by ``zip code tabulation area``.

To claim another variable, add it to ``REQUESTS`` and the Field's module to ``fields``.
"""

import json

from ..core import Crawler, Download, Secret, field_names
from ..fields import (
    population, population_by_gender, population_by_age, children_by_age, population_by_race,
    families_vs_singles, households_with_kids, head_of_household_by_age, housing_type,
    housing_units, occupied_housing_units, housing_occupancy, vacancy_reason,
)

URL = "https://api.census.gov/data/2020/dec/dhc?get={}&for=zip%20code%20tabulation%20area:*"
CENSUS_KEY = Secret(
    env="CENSUS_API_KEY",
    file="~/.census_key",
    signup_url="https://api.census.gov/data/key_signup.html",
    query_param="key",
)
KEY_COLUMN = "zip code tabulation area"


def _numbered(table: str, first: int, last: int):
    return tuple("%s_%03dN" % (table, i) for i in range(first, last + 1))


#: (cached file name, variables); at most 50 variables per request
REQUESTS = (
    ("dhc2020_zcta_tables.json",
     ("P1_001N", "H1_001N", "H3_002N", "H3_003N") + _numbered("H4", 2, 4) + _numbered("H5", 2, 8)
     + _numbered("P3", 2, 8) + ("P16_003N", "P16_005N", "P16_006N", "P16_008N", "P16_009N", "P21_002N", "P21_005N")
     + _numbered("H13", 3, 11) + _numbered("H13", 13, 21)),
    ("dhc2020_zcta_P12.json", _numbered("P12", 2, 49)),
    ("dhc2020_zcta_PCT12.json", _numbered("PCT12", 3, 23) + _numbered("PCT12", 107, 127)),
    ("dhc2020_zcta_PCT19.json",  # 7 facility types x 6 sex and age groups
     tuple("PCT19_%03dN" % (block + offset)
           for offset in (0, 32, 64, 97, 129, 161) for block in (5, 12, 16, 17, 24, 25, 28))),
)
VARIABLES = tuple(v for _, variables in REQUESTS for v in variables)


def parse(files):
    rows = {}
    for filename, _ in REQUESTS:
        with open(files[filename], encoding="utf-8") as fh:
            header, *records = json.load(fh)
        i_key = header.index(KEY_COLUMN)
        for record in records:
            rows.setdefault(record[i_key], {}).update(zip(header, record))
    return iter(rows.items())


CRAWLER = Crawler(
    name="census-dhc",
    fields=field_names(
        population, population_by_gender, population_by_age, children_by_age, population_by_race,
        families_vs_singles, households_with_kids, head_of_household_by_age, housing_type,
        housing_units, occupied_housing_units, housing_occupancy, vacancy_reason,
    ),
    downloads=tuple(Download(filename, URL.format(",".join(variables)), magic=b"[[", secret=CENSUS_KEY)
                    for filename, variables in REQUESTS),
    parse=parse,
    description="2020 Census DHC -> population, housing units and the DHC distributions",
)
