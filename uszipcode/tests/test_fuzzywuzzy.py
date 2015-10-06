#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uszipcode.packages.fuzzywuzzy import process
import unittest

class FuzzyWuzzyUnittest(unittest.TestCase):
    def test_all(self):
        text = "playboy"
        choice = ["a cow boy", "play boy", "playboy magazine"]
        res = process.extract(text, choice)
        self.assertEqual(res[0][0], "play boy")
        self.assertEqual(res[1][0], "playboy magazine")
        self.assertEqual(res[2][0], "a cow boy")
        
if __name__ == "__main__":
    unittest.main()
