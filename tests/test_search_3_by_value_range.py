# -*- coding: utf-8 -*-

import pytest
from uszipcode.tests import SearchEngineBaseTest, assert_descending_by
from uszipcode.search import SearchEngine, ComprehensiveZipcode as Zipcode


class TestSearchEngine(SearchEngineBaseTest):
    search = SearchEngine(
        simple_or_comprehensive=SearchEngine.SimpleOrComprehensiveArgEnum.simple,
    )

    def test_by_range(self):
        test_cases = [
            # tuple: (sort by attr name, lower, upper)
            (Zipcode.population.name, 10000, 50000),
            (Zipcode.population_density.name, 1000, 2000),
            (Zipcode.land_area_in_sqmi.name, 5, 10),
            (Zipcode.water_area_in_sqmi.name, 0.5, 1),
            (Zipcode.housing_units.name, 1000, 2000),
            (Zipcode.occupied_housing_units.name, 1000, 2000),
            (Zipcode.median_home_value.name, 200000, 400000),
            (Zipcode.median_household_income.name, 50000, 60000),
        ]
        for sort_by, lower, upper in test_cases:
            method_name = f"by_{sort_by}"
            method = getattr(self.sr, method_name)
            z_list = method(lower=lower, upper=upper)
            assert len(z_list) > 0
            assert_descending_by(z_list, sort_by)


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
