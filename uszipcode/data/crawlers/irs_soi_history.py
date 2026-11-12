# -*- coding: utf-8 -*-

"""
irs-soi-history: IRS Statistics of Income, ZIP Code Data, every tax year from 2011,
for the history columns. One CSV per tax year (about 40 MB each, no key), the same
files as ``irs-soi``: one row per ZIP and state, all income classes combined; ZIPs
with fewer than 100 returns are pooled as 99999, and 00000 holds the state totals
(both are skipped). The IRS has no file of this form before 2011. A source row is
one line of one year under its column names in upper case (the case of the header
changes between years), with ``year`` set to the tax year.

The file of the latest year is also the download of ``irs-soi``. A history crawler
cannot claim the Fields of the main table, so the two crawlers each download that
one file (the exception of rule C8).

``LAST_YEAR`` should follow ``irs_soi.YEAR``.
"""

import csv

from ..core import Crawler, Download, field_names
from ..fields.history import tax_returns, people_on_tax_returns, average_income_per_return

FIRST_YEAR, LAST_YEAR = 2011, 2023
URL = "https://www.irs.gov/pub/irs-soi/{yy:02d}zpallnoagi.csv"
YEARS = tuple(range(FIRST_YEAR, LAST_YEAR + 1))


def filename(year: int) -> str:
    return "%02dzpallnoagi.csv" % (year % 100)


def parse(files):
    for year in YEARS:
        with open(files[filename(year)], encoding="utf-8", errors="replace", newline="") as fh:
            reader = csv.reader(fh)
            header = [h.strip().upper() for h in next(reader)]
            i_zip = header.index("ZIPCODE")
            for row in reader:
                if len(row) == len(header):
                    yield row[i_zip], dict(zip(header, row), year=year)


CRAWLER = Crawler(
    name="irs-soi-history",
    fields=field_names(tax_returns, people_on_tax_returns, average_income_per_return),
    downloads=tuple(Download(filename(year), URL.format(yy=year % 100), magic=b"STATEFIPS,") for year in YEARS),
    parse=parse,
    description="IRS SOI ZIP Code Data, tax years %d-%d -> tax returns, their people and average income by year"
                % (FIRST_YEAR, LAST_YEAR),
    history=True,
)
