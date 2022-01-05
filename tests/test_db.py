# -*- coding: utf-8 -*-

import pytest
from pathlib_mate import Path
from uszipcode.db import (
    download_db_file,
    SIMPLE_DB_FILE_DOWNLOAD_URL,
    COMPREHENSIVE_DB_FILE_DOWNLOAD_URL,
)

HERE = Path(__file__).parent
DEFAULT_SIMPLE_DB_FILE_PATH = Path(HERE, "simple_db.sqlite")
DEFAULT_COMPREHENSIVE_DB_FILE_PATH = Path(HERE, "comprehensive_db.sqlite")


def setup_module(module):
    DEFAULT_SIMPLE_DB_FILE_PATH.remove_if_exists()
    DEFAULT_COMPREHENSIVE_DB_FILE_PATH.remove_if_exists()


def test_download_db_file():
    download_db_file(
        db_file_path=DEFAULT_SIMPLE_DB_FILE_PATH.abspath,
        download_url=SIMPLE_DB_FILE_DOWNLOAD_URL,
        chunk_size=1024 * 1024,  # 1MB
        progress_size=1024 * 1024,  # 1MB
    )
    download_db_file(
        db_file_path=DEFAULT_COMPREHENSIVE_DB_FILE_PATH.abspath,
        download_url=COMPREHENSIVE_DB_FILE_DOWNLOAD_URL,
        chunk_size=1024 * 1024,  # 1MB
        progress_size=50 * 1024 * 1024,  # 50MB
    )

    pass


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
