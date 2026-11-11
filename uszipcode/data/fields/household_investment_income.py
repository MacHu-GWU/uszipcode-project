# -*- coding: utf-8 -*-

"""
``household_investment_income_*``. Claimed by ``irs-soi``.

Stands for the 2.x fields ``household_investment_income____percent_of_households_receiving_investment_income``
and ``..._average_income_per_household_by_income_source``. The IRS counts tax returns, not
households, and only taxable amounts of filers.
"""

from ..core import share_and_average_group

FIELDS = share_and_average_group(
    "household_investment_income", "IRS SOI ZIP Code Data, tax returns filed from the ZIP", "N1", 1000, (
        ("interest", "taxable interest", "N00300", "A00300"),
        ("ordinary_dividends", "ordinary dividends", "N00600", "A00600"),
        ("qualified_dividends", "qualified dividends", "N00650", "A00650"),
        ("capital_gains", "net capital gain", "N01000", "A01000"),
    ))
