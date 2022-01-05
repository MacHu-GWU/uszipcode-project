# -*- coding: utf-8 -*-

import pytest
from uszipcode.tests import SearchEngineBaseTest
from uszipcode.model import ZipcodeTypeEnum, ComprehensiveZipcode
from uszipcode.search import SearchEngine

class TestSearchEngineCensusData(SearchEngineBaseTest):
    search = SearchEngine(
        simple_or_comprehensive=SearchEngine.SimpleOrComprehensiveArgEnum.comprehensive
    )
    def test(self):
        z = self.search.by_zipcode("10001")
        _ = z.bounds
        if self.search.zip_klass is ComprehensiveZipcode:
            _ = z.population_by_age
            _ = z.head_of_household_by_age
            _ = z.polygon

    def test_by_zipcode_non_standard(self):
        """
        Test by_zipcode should return any type zipcode.
        """
        z = self.search.by_zipcode(48874)
        assert z.zipcode_type != ZipcodeTypeEnum.Standard.value
        assert z.lat is not None


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
