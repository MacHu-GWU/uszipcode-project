# -*- coding: utf-8 -*-

import pytest
from base import TestSearchEngineBase, assert_descending_by
from uszipcode.search import Zipcode


class TestSearchEngineQuery(TestSearchEngineBase):

    def test_by_range(self):
        test_cases = [
            (Zipcode.population.name, 10000, 50000),
            (Zipcode.population_density.name, 1000, 2000),
            (Zipcode.land_area_in_sqmi.name, 5, 10),
            (Zipcode.water_area_in_sqmi.name, 0.5, 1),
            (Zipcode.housing_units.name, 1000, 2000),
            (Zipcode.occupied_housing_units.name, 1000, 2000),
            (Zipcode.median_home_value.name, 200000, 400000),
            (Zipcode.median_household_income.name, 50000, 60000),
        ]
        for field, lower, upper in test_cases:
            func_name = "by_{}".format(field)
            query_func = getattr(self.search, func_name)
            z_list = query_func(lower, upper)
            assert len(z_list) > 0
            assert_descending_by(z_list, field)


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
