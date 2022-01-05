# -*- coding: utf-8 -*-

"""
The dataset for ``uszipcode`` is from multiple source, and integrated by Sanhe Hu.

- 2012-01-22 federal governmanet zipcode data from
  http://federalgovernmentzipcodes.us/
- 2010 zcta2010 population, wage, houseunit, land, water area data from
  from http://proximityone.com/cen2010_zcta_dp.htm
- 2015-10-01 geometry google map geocoding data from http://maps.google.com
"""

import requests
from pathlib_mate import Path
from pathlib_mate.helper import repr_data_size
from atomicwrites import atomic_write
import sqlalchemy_mate as sam

SIMPLE_DB_FILE_DOWNLOAD_URL = "https://github.com/MacHu-GWU/uszipcode-project/releases/download/1.0.1.db/simple_db.sqlite"
COMPREHENSIVE_DB_FILE_DOWNLOAD_URL = "https://github.com/MacHu-GWU/uszipcode-project/releases/download/1.0.1.db/comprehensive_db.sqlite"

USZIPCODE_HOME = Path(Path.home(), ".uszipcode")
DEFAULT_SIMPLE_DB_FILE_PATH = Path(USZIPCODE_HOME, "simple_db.sqlite")
DEFAULT_COMPREHENSIVE_DB_FILE_PATH = Path(USZIPCODE_HOME, "comprehensive_db.sqlite")


def download_db_file(
    db_file_path: str,
    download_url: str,
    chunk_size: int,
    progress_size: int,
):
    Path(db_file_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"Download {db_file_path} from {download_url} ...")
    response = requests.get(download_url, stream=True)

    downloaded_size = 0
    next_log_threshold = progress_size
    with atomic_write(db_file_path, mode="wb", overwrite=True) as f:
        for chunk in response.iter_content(chunk_size):
            if not chunk:
                break
            f.write(chunk)
            downloaded_size += chunk_size
            if downloaded_size >= next_log_threshold:
                print("  {} downloaded ...".format(repr_data_size(downloaded_size)))
                next_log_threshold += progress_size
    print("  Complete!")
