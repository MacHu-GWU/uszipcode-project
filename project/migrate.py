#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Create simple_zipcode database from full data zipcode database.
"""

from sqlalchemy.orm import sessionmaker
from uszipcode.model import Base, Zipcode, SimpleZipcode, _simple_zipcode_columns
from uszipcode.db import connect_to_simple_zipcode_db, connect_to_zipcode_db

simple_zipcode_engine = connect_to_simple_zipcode_db()
Base.metadata.create_all(simple_zipcode_engine)

zipcode_engine = connect_to_zipcode_db()

zipcode_ses = sessionmaker(bind=zipcode_engine)()
selected_columns = [
    getattr(Zipcode, name)
    for name in _simple_zipcode_columns
]
simple_zipcode_data = list()
for data_tuple in zipcode_ses.query(*selected_columns):
    simple_zipcode = SimpleZipcode(**dict(list(zip(_simple_zipcode_columns, data_tuple))))
    simple_zipcode_data.append(simple_zipcode)

SimpleZipcode.smart_insert(simple_zipcode_engine, simple_zipcode_data)
