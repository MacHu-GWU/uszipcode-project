# -*- coding: utf-8 -*-

"""
``sources_of_household_income_*``. Claimed by ``irs-soi``.

Stands for the 2.x fields ``sources_of_household_income____percent_of_households_receiving_income``
and ``..._average_income_per_household_by_income_source``. The IRS counts tax returns, not
households, and only taxable amounts of filers.
"""

from ..core import share_and_average_group

FIELDS = share_and_average_group(
    "sources_of_household_income", "IRS SOI ZIP Code Data, tax returns filed from the ZIP", "N1", 1000, (
        ("wages", "salaries and wages", "N00200", "A00200"),
        ("business", "business or profession net income", "N00900", "A00900"),
        ("partnership_scorp", "partnership or S corporation net income", "N26270", "A26270"),
        ("unemployment", "unemployment compensation", "N02300", "A02300"),
    ))
