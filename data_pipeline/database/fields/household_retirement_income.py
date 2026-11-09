# -*- coding: utf-8 -*-

"""
``household_retirement_income_*``. Claimed by ``irs-soi``.

Stands for the 2.x fields ``household_retirement_income____percent_of_households_receiving_retirement_incom``
and ``..._average_income_per_household_by_income_source``. The IRS counts tax returns, not
households, and only taxable amounts of filers. 2.x showed one "retirement distributions"
share, which was IRA distributions plus pensions and annuities added together (a return
can have both); here they are kept apart.
"""

from ..core import share_and_average_group

FIELDS = share_and_average_group(
    "household_retirement_income", "IRS SOI ZIP Code Data, tax returns filed from the ZIP", "N1", 1000, (
        ("ira_distributions", "taxable IRA distributions", "N01400", "A01400"),
        ("pensions_annuities", "taxable pensions and annuities", "N01700", "A01700"),
        ("social_security", "taxable Social Security benefits", "N02500", "A02500"),
    ))
