# -*- coding: utf-8 -*-

import pytest
import sqlalchemy_mate as sam
from uszipcode.search import SearchEngine, DEFAULT_SIMPLE_DB_FILE_PATH


def test_custom_engine():
    # ensure simple db file exists
    _ = SearchEngine()

    # use custom db engine
    engine = sam.EngineCreator().create_sqlite(path=DEFAULT_SIMPLE_DB_FILE_PATH)
    sr = SearchEngine(engine=engine)
    z = sr.by_zipcode("10001")
    assert z.state == "NY"


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
