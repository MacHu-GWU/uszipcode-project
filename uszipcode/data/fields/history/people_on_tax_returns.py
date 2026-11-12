# -*- coding: utf-8 -*-

"""
``people_on_tax_returns``, history. Claimed by ``irs-soi-history``.

The number of people the tax returns of the ZIP stand for: the taxpayers and their
dependents. The IRS column is ``N2``, which it names "number of exemptions" up to tax
year 2017 and "number of individuals" from 2018, when the personal exemption was
suspended. People who file no return are not in it, so it is lower than the
population. uszipcode 2.x stored this number under the name ``population_by_year``.
"""

from ...core import Field, column, parse_count

FIELDS = (
    Field(
        name="people_on_tax_returns",
        dtype=int,
        description="Number of people on the individual income tax returns filed from the ZIP for that tax year, "
                    "taxpayers and dependents: exemptions up to 2017, individuals from 2018 (IRS SOI ZIP Code Data, "
                    "N2); lower than the population, because not everybody files a return",
        unit="people",
        extract=column("N2", parse_count),
        examples=(({"year": 2018, "N2": "6320.0000"}, 6320), ({"year": 2011, "N2": "6338.0000"}, 6338),
                  ({"year": 2018, "N2": ""}, None)),
    ),
)
