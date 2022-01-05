# -*- coding: utf-8 -*-

import pytest
from uszipcode.tests import SearchEngineBaseTest
from uszipcode.search import SearchEngine


class TestSearchEngineQuery(SearchEngineBaseTest):
    search = SearchEngine(
        simple_or_comprehensive=SearchEngine.SimpleOrComprehensiveArgEnum.simple
    )

    def test_by_zipcode(self):
        z = self.sr.by_zipcode("94103")
        assert z.city == "San Francisco"
        assert z.state == "CA"

if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
