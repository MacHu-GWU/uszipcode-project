#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from base import TestSearchEngineBase
from uszipcode.model import Zipcode, ZipcodeType


class TestSearchEngineCensusData(TestSearchEngineBase):
    def test(self):
        z = self.search.by_zipcode("10001")
        z.bounds
        if self.search.zip_klass is Zipcode:
            z.population_by_age
            z.head_of_household_by_age
            z.polygon

    def test_by_zipcode_non_standard(self):
        """
        Test by_zipcode should return any type zipcode.
        """
        z = self.search.by_zipcode(48874)
        assert z.zipcode_type != ZipcodeType.Standard
        assert z.lat is not None


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
