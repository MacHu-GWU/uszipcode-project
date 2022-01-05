# -*- coding: utf-8 -*-

from uszipcode.search import SearchEngine


def assert_ascending(array):
    """
    Assert that this is a strictly asceding array.
    """
    for i, j in zip(array[1:], array[:-1]):
        if (i is not None) and (j is not None):
            assert i >= j


def assert_descending(array):
    """
    Assert that this is a strictly descending array.
    """
    for i, j in zip(array[1:], array[:-1]):
        if (i is not None) and (j is not None):
            assert i <= j


def assert_ascending_by(zipcode_list, attr):
    """
    Assert that zipcode is ascending ordered by defined attributes
    """
    assert_ascending([getattr(z, attr) for z in zipcode_list])


def assert_descending_by(zipcode_list, attr):
    """
    Assert that zipcode is descending ordered by defined attributes
    """
    assert_descending([getattr(z, attr) for z in zipcode_list])


class SearchEngineBaseTest(object):
    search: SearchEngine = None

    @classmethod
    def teardown_class(cls):
        cls.search.close()

    @property
    def sr(self) -> SearchEngine:
        return self.search