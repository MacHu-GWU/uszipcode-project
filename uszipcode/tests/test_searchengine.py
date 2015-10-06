#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uszipcode.searchengine import ZipcodeSearchEngine
from pprint import pprint as ppt
import unittest

class ZipcodeSearchEngineUnittest(unittest.TestCase):
    """uszipcode.searchengine unittest.
    """
    def test_all(self):
        with ZipcodeSearchEngine() as search:
            zipcode = search.by_zipcode(20876)
            self.assertEqual(zipcode.Zipcode, "20876")
            self.assertEqual(zipcode.City, "Germantown")
            self.assertEqual(zipcode.State, "MD")
             
            res = search.by_coordinate(39.122229, -77.133578, radius=30)
            zipcode = res[0]
            self.assertEqual(zipcode.Zipcode, "20855")
            self.assertEqual(zipcode.City, "Derwood")
            self.assertEqual(zipcode.State, "MD")
            
            res = search.by_coordinate(39.122229, -77.133578, radius=100, 
                                       returns=0)
            self.assertEqual(len(res), 3531)
             
            res = search.by_city_and_state("kersen", "kensas")
            zipcode = res[0]
            self.assertEqual(zipcode.Zipcode, "67561")
            self.assertEqual(zipcode.City, "Nickerson")
            self.assertEqual(zipcode.State, "KS")
            
            res = search.by_prefix("208",
                sortby="Population", descending=True, returns=0)
            self.assertEqual(len(res), 34)

            res = search.by_pattern("100",
                sortby="Population", descending=True, returns=0)
            self.assertEqual(len(res), 97)

            res = search.by_population(lower=100000,
                sortby="Population", descending=True, returns=0)
            self.assertEqual(len(res), 10)
            
            res = search.by_density(lower=10000,
                sortby="Population", descending=True, returns=0)
            self.assertEqual(len(res), 631)
            
            res = search.by_totalwages(lower=1000**3,
                sortby="Population", descending=True, returns=0)
            self.assertEqual(len(res), 155)
            
            res = search.by_wealthy(lower=100000,
                sortby="Population", descending=True, returns=0)
            self.assertEqual(len(res), 41)

            res = search.by_house(lower=20000,
                sortby="Population", descending=True, returns=0)
            self.assertEqual(len(res), 741)
    
    def test_edge_case(self):
        with ZipcodeSearchEngine() as search: 
            zipcode = search.by_zipcode(00000)
            self.assertIsNone(zipcode)
            
            res = search.by_coordinate(39.122229, -77.133578, radius=0.01)
            self.assertEqual(res, [])
            
            res = search.by_city_and_state("unknown", "MD")
            self.assertEqual(res, [])
            
            res = search.by_prefix("00000")
            self.assertEqual(res, [])

            res = search.by_pattern("00000")
            self.assertEqual(res, [])
            
            res = search.by_population(upper=-1)
            self.assertEqual(res, [])
            
            res = search.by_density(upper=-1)
            self.assertEqual(res, [])
            
            res = search.by_totalwages(upper=-1)
            self.assertEqual(res, [])
            
            res = search.by_wealthy(upper=-1)
            self.assertEqual(res, [])

            res = search.by_house(upper=-1)
            self.assertEqual(res, [])
            
if __name__ == "__main__":
    unittest.main()