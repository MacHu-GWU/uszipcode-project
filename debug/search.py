# -*- coding: utf-8 -*-

from uszipcode.search import SearchEngine, ComprehensiveZipcode

with SearchEngine(
    simple_or_comprehensive=SearchEngine.SimpleOrComprehensiveArgEnum.comprehensive,
) as sr:
    # res = sr.find_state(state="virgnea", best_match=True)
    # res = sr.find_city(city="arlingten", state="virgnea", best_match=True)
    # res = sr.find_city("G&w!3Vt@tt8v", best_match=False)
    # print(res)
    # print(sr.state_to_city_mapper["VA"])
    z = sr.by_zipcode(zipcode="22201")
    print(z)