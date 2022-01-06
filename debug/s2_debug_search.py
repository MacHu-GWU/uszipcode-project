# -*- coding: utf-8 -*-

from uszipcode.search import SearchEngine, ComprehensiveZipcode

with SearchEngine(
    simple_or_comprehensive=SearchEngine.SimpleOrComprehensiveArgEnum.comprehensive,
) as sr:
    res = sr.find_state(state="virgnea", best_match=True)
    res = sr.find_city(city="arlingten", state="virgnea", best_match=True)
    print(res)
    z = sr.by_zipcode(zipcode="22201")
    print(z)