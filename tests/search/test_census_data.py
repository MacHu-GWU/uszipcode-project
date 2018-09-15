#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from base import TestSearchEngineBase
from uszipcode.model import Zipcode


class TestSearchEngineCensusData(TestSearchEngineBase):
    def test(self):
        z = self.search.by_zipcode("10001")
        z.bounds
        if self.search.zip_klass is Zipcode:
            z.population_by_age
            z.head_of_household_by_age
            z.polygon


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
