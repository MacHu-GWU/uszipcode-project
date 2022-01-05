# -*- coding: utf-8 -*-

import pytest
from uszipcode.tests import SearchEngineBaseTest
from uszipcode.state_abbr import MAPPER_STATE_ABBR_SHORT_TO_LONG, MAPPER_STATE_ABBR_LONG_TO_SHORT
from uszipcode.search import SearchEngine

PASSWORD = "yFTFNgn%vMPQcQGjmU8DxmQt3@b7iB5P"


class TestSearchEngine(SearchEngineBaseTest):
    search = SearchEngine(
        simple_or_comprehensive=SearchEngine.SimpleOrComprehensiveArgEnum.simple,
    )

    def test_cached_data(self):
        assert self.search.city_list[0].startswith("A")
        assert self.search.state_list[0].startswith("A")
        assert len(self.search.city_to_state_mapper) >= 1
        assert len(self.search.state_to_city_mapper) >= 1

    def test_find_state(self):
        for state_short in MAPPER_STATE_ABBR_SHORT_TO_LONG:
            assert self.search.find_state(
                state_short.lower(), best_match=True
            )[0] == state_short

        for state_long in MAPPER_STATE_ABBR_LONG_TO_SHORT:
            assert self.search.find_state(
                state_long.lower()[:8], best_match=True
            )[0] == MAPPER_STATE_ABBR_LONG_TO_SHORT[state_long]

        assert self.search.find_state("mary", best_match=True) == ["MD", ]

        result = set(self.search.find_state("virgin", best_match=False))
        assert result == {"VI", "WV", "VA"}

        assert self.search.find_state("neyork", best_match=False) == ["NY", ]

        with pytest.raises(ValueError):
            self.search.find_state("THIS IS NOT A STATE!", best_match=True)

        with pytest.raises(ValueError):
            self.search.find_state("THIS IS NOT A STATE!", best_match=False)

    def test_find_city(self):
        city_result = self.search.find_city("phonix", best_match=True)
        city_expected = ["Phoenix", ]
        assert city_result == city_expected

        city_result = self.search.find_city("kerson", best_match=False)
        city_result.sort()
        city_expected = [
            "Dickerson", "Dickerson Run",
            "Emerson", "Ericson", "Everson", "Keldron", "Nickerson",
        ]
        for city in city_result:
            assert city in city_expected

        with pytest.raises(ValueError):
            self.search.find_city(PASSWORD, best_match=False)

        city_result = self.search.find_city(
            "kersen", state="kensas", best_match=False
        )
        city_expected = ["Nickerson", ]
        assert city_result == city_expected

    def test_by_city(self):
        res = self.search.by_city("vienna")
        s = set()
        for z in res:
            assert z.major_city == "Vienna"
            s.add(z.state_abbr)

        res = self.search.by_city(PASSWORD)
        assert len(res) == 0

    def test_by_state(self):
        res = self.search.by_state("ca")
        assert len(res) > 0
        for z in res:
            assert z.state_abbr == "CA"

        res = self.search.by_state("ilinoy")
        assert len(res) > 0
        for z in res:
            assert z.state_abbr == "IL"

    def test_by_city_and_state(self):
        # Arlington, VA
        res = self.search.by_city_and_state(city="arlingten", state="virgnea")
        assert len(res) > 0
        for z in res:
            assert z.major_city == "Arlington"
            assert z.state_abbr == "VA"

    def test_edge_case(self):
        zipcode = self.search.by_zipcode(0)
        assert bool(zipcode) is False

        # Use White House in DC
        lat, lng = 38.897835, -77.036541
        res = self.search.by_coordinates(lat, lng, radius=0.01)
        assert len(res) == 0

        # Use Eiffel Tower in Paris
        lat, lng = 48.858388, 2.294581
        res = self.search.by_coordinates(lat, lng, radius=0.01)
        assert len(res) == 0

        res = self.search.by_city_and_state("Unknown", "MD")
        assert len(res) == 0

        res = self.search.by_prefix("00000")
        assert len(res) == 0

        res = self.search.by_pattern("00000")
        assert len(res) == 0

        res = self.search.by_population(upper=-1)
        assert len(res) == 0

    def test_bad_param(self):
        with pytest.raises(ValueError):
            self.search.query(zipcode="10001", prefix="10001", pattern="10001")

        with pytest.raises(ValueError):
            self.search.query(lat=34, lng=-72)


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
