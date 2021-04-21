# -*- coding: utf-8 -*-

import pytest
from base import TestSearchEngineBase
from uszipcode.model import Zipcode, ZipcodeType


class TestSearchEngineCensusData(TestSearchEngineBase):
    def test(self):
        print(len(self.search.all(returns=100)))

if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
