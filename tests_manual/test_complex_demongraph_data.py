# -*- coding: utf-8 -*-

import pytest
from uszipcode.search import SearchEngine


class TestComplexSearchEngineBase(object):
    search = None

    @classmethod
    def setup_class(cls):
        cls.search = SearchEngine(simple_zipcode=False)

    @classmethod
    def teardown_class(cls):
        cls.search.close()


class TestSearchEngineCensusData(TestComplexSearchEngineBase):
    def test(self):
        z = self.search.by_zipcode("10001")
        assert isinstance(z.population_by_year, list)


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
