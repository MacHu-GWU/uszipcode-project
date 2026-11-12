# -*- coding: utf-8 -*-

"""
``average_income_per_return``, history. Claimed by ``irs-soi-history``.

The adjusted gross income of all returns of the ZIP, divided by their number. It is
an average per tax return, not per household and not per person, and a few very
large incomes move it far more than they would move a median. uszipcode 2.x stored
this number under the name ``average_household_income_over_time``.
"""

from ...core import Field, ratio

FIELDS = (
    Field(
        name="average_income_per_return",
        dtype=int,
        description="Average adjusted gross income per individual income tax return filed from the ZIP for that "
                    "tax year, in dollars of that year (IRS SOI ZIP Code Data, A00100 x 1,000 / N1)",
        unit="dollars",
        extract=ratio("A00100", "N1", scale=1000, whole=True),
        examples=(({"year": 2018, "A00100": "915227.0000", "N1": "5220.0000"}, 175331),
                  ({"year": 2018, "A00100": "5000", "N1": "0"}, None),
                  ({"year": 2018, "A00100": "", "N1": "100"}, None)),
    ),
)
