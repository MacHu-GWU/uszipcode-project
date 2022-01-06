# -*- coding: utf-8 -*-

import pytest


def test():
    import uszipcode

    _ = uszipcode.SearchEngine
    _ = uszipcode.SimpleZipcode
    _ = uszipcode.ComprehensiveZipcode
    _ = uszipcode.ZipcodeTypeEnum
    _ = uszipcode.SORT_BY_DIST


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
