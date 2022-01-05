# -*- coding: utf-8 -*-

import pytest
from uszipcode.tests import (
    SearchEngineBaseTest,
    assert_ascending, assert_descending,
    assert_ascending_by, assert_descending_by,
)
from uszipcode.search import (
    SearchEngine,
    ComprehensiveZipcode as Zipcode,
    ZipcodeTypeEnum,
    SORT_BY_DIST, DEFAULT_LIMIT,
)


class TestSearchEngine(SearchEngineBaseTest):
    search = SearchEngine(
        simple_or_comprehensive=SearchEngine.SimpleOrComprehensiveArgEnum.simple,
    )

    def test_resolve_sort_by(self):
        with pytest.raises(ValueError):
            self.search._resolve_sort_by(
                "InValid Field", flag_radius_query=True)

        with pytest.raises(ValueError):
            self.search._resolve_sort_by(
                "InValid Field", flag_radius_query=False)

        assert self.search._resolve_sort_by(
            Zipcode.zipcode, flag_radius_query=True
        ) == Zipcode.zipcode.name

        assert self.search._resolve_sort_by(
            Zipcode.population, flag_radius_query=True
        ) == Zipcode.population.name

        assert self.search._resolve_sort_by(
            Zipcode.zipcode, flag_radius_query=False
        ) == Zipcode.zipcode.name

        assert self.search._resolve_sort_by(
            Zipcode.population, flag_radius_query=False
        ) == Zipcode.population.name

        assert self.search._resolve_sort_by(
            None, flag_radius_query=True
        ) == SORT_BY_DIST

        assert self.search._resolve_sort_by(
            None, flag_radius_query=False
        ) == None

        assert self.search._resolve_sort_by(
            SORT_BY_DIST, flag_radius_query=True
        ) == SORT_BY_DIST

        with pytest.raises(ValueError):
            self.search._resolve_sort_by(SORT_BY_DIST, flag_radius_query=False)

    def test_by_zipcode(self):
        z = self.search.by_zipcode("10001")
        assert z.zipcode == "10001"
        assert z.major_city == "New York"
        assert z.zipcode_type == ZipcodeTypeEnum.Standard.value

        z = self.search.by_zipcode("123456789")
        assert bool(z) is False

    def test_by_prefix(self):
        z_list = self.search.by_prefix("100", ascending=True)
        assert_ascending_by(z_list, Zipcode.zipcode.name)

        z_list = self.search.by_prefix("100", ascending=False)
        assert_descending_by(z_list, Zipcode.zipcode.name)

        for z in z_list:
            assert z.zipcode.startswith("100")

    def test_by_pattern(self):
        z_list = self.search.by_pattern("001")
        for z in z_list:
            assert "001" in z.zipcode

    def test_no_limit(self):
        res = self.search.by_prefix("1000", returns=None)
        assert len(res) > 0

    def test_by_coordinates(self):
        # Use White House in DC
        lat, lng = 38.897835, -77.036541

        res1 = self.search.by_coordinates(lat, lng, ascending=True)
        assert len(res1) <= DEFAULT_LIMIT

        dist_array = [z.dist_from(lat, lng) for z in res1]
        assert_ascending(dist_array)

        res2 = self.search.by_coordinates(lat, lng, ascending=False)
        dist_array = [z.dist_from(lat, lng) for z in res2]
        assert_descending(dist_array)

        # returns everything when `returns = 0`
        res3 = self.search.by_coordinates(lat, lng, ascending=True, returns=0)
        assert len(res3) > len(res1)

        res4 = self.search.by_coordinates(lat, lng, ascending=False, returns=0)
        assert len(res4) > len(res1)

        # sort by other field
        res5 = self.search.by_coordinates(
            lat, lng, radius=5, sort_by=Zipcode.zipcode.name)
        for z in res5:
            assert z.dist_from(lat, lng) <= 5
        assert_ascending_by(res5, Zipcode.zipcode.name)

        # when no zipcode matching criterion, return empty list
        # Use Eiffel Tower in Paris
        lat, lng = 48.858388, 2.294581
        res6 = self.search.by_coordinates(lat, lng)
        assert len(res6) == 0


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
