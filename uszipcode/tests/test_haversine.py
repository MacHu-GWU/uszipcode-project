#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uszipcode.packages.haversine import great_circle
import unittest

class HaversineUnittest(unittest.TestCase):
    def test_all(self):
        lyon = (45.7597, 4.8422)
        paris = (48.8567, 2.3508)

        self.assertAlmostEqual(
            great_circle(lyon, paris, miles=False)/392.001248, 1.0, delta=0.01)
        self.assertAlmostEqual(
            great_circle(lyon, paris, miles=True)/243.589575, 1.0, delta=0.01)
  
if __name__ == "__main__":
    unittest.main()