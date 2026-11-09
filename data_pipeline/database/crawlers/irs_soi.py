# -*- coding: utf-8 -*-

"""
irs-soi: IRS Statistics of Income, ZIP Code Data, latest published tax year.

One CSV per tax year (about 40 MB, no key) with one row per ZIP and state, all
income classes combined. Its ZIPs are those taxpayers write on their returns, not
ZCTAs; ZIPs with fewer than 100 returns are pooled as 99999, and 00000 holds the
state totals (both are skipped). Counts are rounded to 10 and amounts are in
thousands of dollars. A source row is one line under its column names in upper
case (the case of the header changes between years).
"""

import csv

from ..core import Crawler, Download, field_names
from ..fields import sources_of_household_income, household_investment_income, household_retirement_income

YEAR = 2023
URL = "https://www.irs.gov/pub/irs-soi/{yy:02d}zpallnoagi.csv"


def filename(year: int) -> str:
    return "%02dzpallnoagi.csv" % (year % 100)


def parse_for(year: int):
    def parse(files):
        with open(files[filename(year)], encoding="utf-8", errors="replace", newline="") as fh:
            reader = csv.reader(fh)
            header = [h.strip().upper() for h in next(reader)]
            i_zip = header.index("ZIPCODE")
            for row in reader:
                if len(row) == len(header):
                    yield row[i_zip], dict(zip(header, row))
    return parse


def crawler_for(year: int) -> Crawler:
    """The crawler for one tax year (``CRAWLER`` is the latest)."""
    return Crawler(
        name="irs-soi",
        fields=field_names(sources_of_household_income, household_investment_income, household_retirement_income),
        downloads=(Download(filename(year), URL.format(yy=year % 100), magic=b"STATEFIPS,"),),
        parse=parse_for(year),
        description="IRS SOI ZIP Code Data, tax year %d -> shares and averages of 11 income sources" % year,
    )


CRAWLER = crawler_for(YEAR)
