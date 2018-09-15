#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uszipcode import SearchEngine, SORT_BY_DIST

search = SearchEngine(simple_zipcode=True)
zipcode = search.by_zipcode("10001")
# print(zipcode)
# print(zipcode.to_dict())
# print(zipcode.to_json())
# print(zipcode.values())
