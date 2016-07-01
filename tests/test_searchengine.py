#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from uszipcode.searchengine import Zipcode, ZipcodeSearchEngine
from uszipcode.packages.haversine import great_circle


def is_all_ascending(array):
    """Assert that this is a strictly asceding array.
    """
    for i, j in zip(array[1:], array[:-1]):
        if (i is not None) and (j is not None):
            assert i - j >= 0

def is_all_descending(array):
    """Assert that this is a strictly desceding array.
    """
    for i, j in zip(array[1:], array[:-1]):
        if (i is not None) and (j is not None):
            assert i - j <= 0


class TestZipcode(object):
    def test_init(self):
        z = Zipcode(Zipcode="10001")
        assert z.Zipcode == "10001"
        assert z.ZipcodeType is None

    def test_make(self):
        z = Zipcode._make(["Zipcode", ], ["10001", ])
        assert z.Zipcode == "10001"
        assert z.ZipcodeType is None

    def test_hash(self):
        z1 = Zipcode(Zipcode="10001")
        z2 = Zipcode(Zipcode="10001")
        assert hash(z1) == hash(z2)
        assert hash(Zipcode())

        s = set([z1, z2])
        assert len(s) == 1

    def test_compare(self):
        z1 = Zipcode(Zipcode="10001")
        z2 = Zipcode(Zipcode="10002")
        z3 = Zipcode()

        assert z1 == z1
        assert z1 != z2
        assert z1 < z2
        assert z2 >= z1

        with pytest.raises(ValueError):
            z1 > z3
        with pytest.raises(ValueError):
            z3 > z3

    def test_iter(self):
        z = Zipcode()
        for i in list(z):
            assert i is None

        for i, j in zip(z.keys(), Zipcode.__keys__):
            assert i == j

    def test_output(self):
        z = Zipcode(Zipcode="10001", ZipcodeType="Standard")


class TestZipcodeSearchEngine(object):
    def test_sql_create_order_by(self):
        with ZipcodeSearchEngine() as search:
            sql = search._sql_create_order_by("Zipcode", True)
            assert sql == "\n\tORDER BY Zipcode ASC"

            sql = search._sql_create_order_by(
                ["latitude", "longitude"], [False, False])
            assert sql == "\n\tORDER BY Latitude DESC, Longitude DESC"

            sql = search._sql_create_order_by("Hello", True)
            assert sql == ""

    def test_sql_create_limit(self):
        with ZipcodeSearchEngine() as search:
            sql = search._sql_create_limit(1)
            assert sql == "\n\tLIMIT 1"

            sql = search._sql_create_limit(0)
            assert sql == ""

    def test_sql_create_lower_upper(self):
        with ZipcodeSearchEngine() as search:
            with pytest.raises(ValueError):
                sql = search._sql_create_lower_upper("Population", None, None)
            with pytest.raises(ValueError):
                sql = search._sql_create_lower_upper("Population", "SQL", "SQL")
            
            sql = search._sql_create_lower_upper("Population", 0, None)
            assert sql == "Population >= 0"
            
            sql = search._sql_create_lower_upper("Population", None, 999999)
            assert sql == "Population <= 999999"
            
            sql = search._sql_create_lower_upper("Population", 0, 999999)
            assert sql == "Population >= 0 AND Population <= 999999"
            
    def test_search_by_zipcode(self):
        with ZipcodeSearchEngine() as search:
            for zipcode in [10001, "10001"]:
                z = search.by_zipcode(zipcode)
                assert z.Zipcode == "10001"
                assert z.State == "NY"
                assert z.City == "New York"

            z = search.by_zipcode(99999)
            assert bool(z) is False

    def test_search_by_coordinate(self):
        with ZipcodeSearchEngine() as search:
            # 在马里兰选一个坐标, 返回1000条, 但实际上不到1000条
            lat, lng = 39.114407, -77.205758
            
            # 返回的结果必须按照距离是从小到大的
            res1 = search.by_coordinate(lat, lng, ascending=True, returns=1000)
            len(res1) < 1000
            dist_array = [great_circle((lat, lng), (z.Latitude, z.Longitude), miles=True) for z in res1]
            is_all_ascending(dist_array)
            
            res2 = search.by_coordinate(lat, lng, ascending=False, returns=1000)
            dist_array = [great_circle((lat, lng), (z.Latitude, z.Longitude), miles=True) for z in res2]
            is_all_descending(dist_array)
            
            # 当returns = 0时, 返回所有符合条件的
            res3 = search.by_coordinate(lat, lng, returns=0)
            assert len(res1) == len(res3)

            # 当没有符合条件的zipcode时, 返回空列表
            res3 = search.by_coordinate(lat, lng, radius=-1)
            assert len(res3) == 0
            
    def test_find_state(self):
        with ZipcodeSearchEngine() as search:
            assert search._find_state("mary", best_match=True) == ["MD", ]
 
            result = set(search._find_state("virgin", best_match=False))
            assert result == set(["VI", "WV", "VA"])
 
            assert search._find_state("newyork", best_match=False) == ["NY", ]
 
            with pytest.raises(ValueError):
                search._find_state("THIS IS NOT A STATE!", best_match=True)
 
            with pytest.raises(ValueError):
                search._find_state("THIS IS NOT A STATE!", best_match=False)
 
    def test_find_city(self):
        with ZipcodeSearchEngine() as search:
            assert search._find_city("phonix", best_match=True) == [
                "Phoenix", ]
            assert search._find_city("kerson", best_match=False) == [
                "Dickerson Run", "Dickerson", "Nickerson", "Emerson", "Everson"
            ]
            assert search._find_city("kersen", state="kensas", best_match=False) == [
                "Nickerson", ]
 
    def test_by_city_and_state(self):
        with ZipcodeSearchEngine() as search:
            # Arlington, VA
            res = search.by_city_and_state(city="arlingten", state="virgnea")
            for z in res:
                z.City == "Arlington"
                z.State == "VA"
            assert len(res) == 5
 
            # There's no city in VI
            with pytest.raises(ValueError):
                search.by_city_and_state(city="Arlington", state="vi")
 
    def test_by_city(self):
        with ZipcodeSearchEngine() as search:
            res = search.by_city("vienna")
            s = set()
            for z in res:
                assert z.City == "Vienna"
                s.add(z.State)
            assert s == set(["ME", "MD", "VA"])
 
    def test_by_state(self):
        with ZipcodeSearchEngine() as search:
            res = search.by_state("RI")
            z = res[0]
            assert z.Zipcode == "02804"
            assert z.City == "Ashaway"
            assert z.State == "RI"

    def test_by_prefix(self):
        """Test sort_by, ascending keyword.
        """
        with ZipcodeSearchEngine() as search:
            prefix = "208"
            sort_key = "Population"
            res = search.by_prefix(prefix,
                                   sort_by=sort_key, ascending=True, returns=0)
            l = list()
            for z in res:
                assert z.Zipcode.startswith(prefix) # example prefix
                l.append(z[sort_key])
            l_sorted = list(l)
            l_sorted.sort()
            assert l == l_sorted

            res = search.by_prefix("100",
                                   sort_by=["Wealthy", ], ascending=[False, ])

    def test_by_pattern(self):
        with ZipcodeSearchEngine() as search:
            res = search.by_pattern("100", returns=0)
            assert len(res) == 97

    def test_by_density(self):
        with ZipcodeSearchEngine() as search:
            res = search.by_density(lower=10000,
                                    sort_by="Density", ascending=False, returns=0)
            assert len(res) == 631

    def test_by_landarea(self):
        with ZipcodeSearchEngine() as search:
            res = search.by_landarea(lower=1000,
                                     sort_by="LandArea", ascending=False, returns=0)
            assert len(res) == 181

    def test_by_waterarea(self):
        with ZipcodeSearchEngine() as search:
            res = search.by_waterarea(lower=100,
                                      sort_by="WaterArea", ascending=False, returns=0)
            assert len(res) == 30

    def test_by_totalwages(self):
        with ZipcodeSearchEngine() as search:
            res = search.by_totalwages(lower=1000**3,
                                       sort_by="TotalWages", ascending=False, returns=0)
            assert len(res) == 155

    def test_by_wealthy(self):
        with ZipcodeSearchEngine() as search:
            res = search.by_wealthy(lower=100000,
                                    sort_by="Wealthy", ascending=False, returns=0)
            assert len(res) == 41

    def test_by_house(self):
        with ZipcodeSearchEngine() as search:
            res = search.by_house(lower=20000,
                                  sort_by="HouseOfUnits", ascending=False, returns=0)
            assert len(res) == 741
    
    def test_find(self):            
        with ZipcodeSearchEngine() as search:
            # Find most people living zipcode in New York
            res = search.find(
                city="new york",
                sort_by="Population", ascending=False,
            )
            is_all_descending([z.Population for z in res])
            
            # Find all zipcode in California that prefix is "999"
            res = search.find(
                state="califor",
                prefix="95",
                sort_by="HouseOfUnits", ascending=False,
                returns=100,
            )
            assert len(res) == 100
            for z in res:
                assert z.State == "CA"
                assert z.Zipcode.startswith("95")
            is_all_descending([z.HouseOfUnits for z in res])
            
            # Find top 10 richest zipcode near Silicon Valley
            lat, lng = 37.391184, -122.082235
            radius = 100
            res = search.find(
                lat=lat, 
                lng=lng,
                radius=radius,
                sort_by="Wealthy", ascending=False,
                returns=10,
            )
            assert len(res) == 10
            for z in res:
                assert great_circle((lat, lng), (z.Latitude, z.Longitude)) <= radius
            is_all_descending([z.Wealthy for z in res])
            
            # Find zipcode that average personal annual income greater than 
            # 100000 near Silicon Valley, order by distance 
            lat, lng = 37.391184, -122.082235
            radius = 100
            res = search.find(
                lat=lat, 
                lng=lng,
                radius=radius,
                wealthy_lower=60000,
                sort_by=None,
                returns=0,
            )
            assert len(res) > 5
            for z in res:
                assert z.Wealthy >= 60000
            is_all_ascending([
                great_circle((lat, lng), (z.Latitude, z.Longitude)) for z in res
            ])
            
    def test_edge_case(self):
        with ZipcodeSearchEngine() as search:
            zipcode = search.by_zipcode(00000)
            assert bool(zipcode) is False

            res = search.by_coordinate(39.122229, -77.133578, radius=0.01)
            assert res == []

            res = search.by_city_and_state("unknown", "MD")
            assert res == []

            res = search.by_prefix("00000")
            assert res == []

            res = search.by_pattern("00000")
            assert res == []

            res = search.by_population(upper=-1)
            assert res == []

            res = search.by_density(upper=-1)
            assert res == []

            res = search.by_totalwages(upper=-1)
            assert res == []

            res = search.by_wealthy(upper=-1)
            assert res == []

            res = search.by_house(upper=-1)
            assert res == []

#--- Unittest ---
if __name__ == "__main__":
    import py
    import os
    py.test.cmdline.main("%s --tb=native -s" % os.path.basename(__file__))
