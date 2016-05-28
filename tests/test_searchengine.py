#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uszipcode.searchengine import ZipcodeSearchEngine
from pprint import pprint as ppt


def test_ZipcodeSearchEngine():
    with ZipcodeSearchEngine() as search:
        zipcode = search.by_zipcode(20876)
        assert zipcode.Zipcode == "20876"
        assert zipcode.City == "Germantown"
        assert zipcode.State == "MD"
         
        res = search.by_coordinate(39.122229, -77.133578, radius=30)
        zipcode = res[0]
        assert zipcode.Zipcode == "20855"
        assert zipcode.City == "Derwood"
        assert zipcode.State == "MD"
        
        res = search.by_coordinate(39.122229, -77.133578, radius=100, returns=0)
        assert len(res) == 3531
         
        res = search.by_city_and_state("kersen", "kensas")
        zipcode = res[0]
        assert zipcode.Zipcode == "67561"
        assert zipcode.City == "Nickerson"
        assert zipcode.State == "KS"
        
        res = search.by_state("RI")
        zipcode = res[0]
        assert zipcode.Zipcode == "02804"
        assert zipcode.City == "Ashaway"
        assert zipcode.State == "RI"

        res = search.by_city("Vienna")
        zipcode = res[0]
        assert zipcode.Zipcode == "04360"
        assert zipcode.City == "Vienna"
        assert zipcode.State == "ME"
                 
        res = search.by_prefix("208",
            sortby="Zipcode", descending=True, returns=0)
        assert len(res) == 34

        res = search.by_pattern("100",
            sortby="Zipcode", descending=True, returns=0)
        assert len(res) == 97

        res = search.by_population(lower=100000,
            sortby="Population", descending=False, returns=0)
        assert len(res) == 10
        
        res = search.by_density(lower=10000,
            sortby="Density", descending=False, returns=0)
        assert len(res) == 631

        res = search.by_landarea(lower=1000,
            sortby="LandArea", descending=False, returns=0)
        assert len(res) == 181

        res = search.by_waterarea(lower=100,
            sortby="WaterArea", descending=False, returns=0)
        assert len(res) == 30
        
        res = search.by_totalwages(lower=1000**3,
            sortby="Population", descending=True, returns=0)
        assert len(res) == 155
        
        res = search.by_wealthy(lower=100000,
            sortby="Population", descending=True, returns=0)
        assert len(res) == 41

        res = search.by_house(lower=20000,
            sortby="Population", descending=True, returns=0)
        assert len(res) == 741


def test_edge_case():
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


if __name__ == "__main__":
    import py
    py.test.cmdline.main("--tb=native -s")