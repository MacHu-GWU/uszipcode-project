# -*- coding: utf-8 -*-

"""
Count number of zipcode for each type.
"""

import sqlalchemy as sa
import sqlalchemy_mate as sam
from uszipcode.search import SearchEngine, SimpleZipcode

with SearchEngine(
    simple_or_comprehensive=SearchEngine.SimpleOrComprehensiveArgEnum.simple,
) as sr:
    n_zipcode = SimpleZipcode.count_all(sr.ses) * 1.0
    stmt = sa.select(
        SimpleZipcode.zipcode_type,
        sa.func.count(SimpleZipcode.zipcode),
        (sa.func.round(sa.func.count(SimpleZipcode.zipcode) / n_zipcode * 10000) / 100).label("percentage")
    ) \
        .group_by(SimpleZipcode.zipcode_type) \
        .order_by(sa.func.count(SimpleZipcode.zipcode).desc())
    res = sr.ses.execute(stmt)
    print(sam.pt.from_result(res))