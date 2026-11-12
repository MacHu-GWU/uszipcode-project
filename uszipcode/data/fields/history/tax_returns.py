# -*- coding: utf-8 -*-

"""
``tax_returns``, history. Claimed by ``irs-soi-history``.

The number of individual income tax returns filed from the ZIP for that tax year. It
counts returns, not people and not households: a couple filing jointly is one return.
"""

from ...core import Field, column, parse_count

FIELDS = (
    Field(
        name="tax_returns",
        dtype=int,
        description="Number of individual income tax returns filed from the ZIP for that tax year, rounded to 10 "
                    "by the IRS (SOI ZIP Code Data, N1); the ZIP is the one on the return, not a ZCTA",
        unit="returns",
        extract=column("N1", parse_count),
        examples=(({"year": 2018, "N1": "5220.0000"}, 5220), ({"year": 2011, "N1": "5316"}, 5316),
                  ({"year": 2018, "N1": ""}, None)),
    ),
)
