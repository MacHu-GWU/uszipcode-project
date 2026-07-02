# -*- coding: utf-8 -*-

"""
Yet the best united state zipcode programming database in Python.
"""

from ._version import __version__

__short_description__ = (
    "USA zipcode programmable database, includes "
    "2020 census data and geometry information."
)
__license__ = "MIT"
__author__ = "Eric Schles"
__author_email__ = "ericschles@gmail.com"
__maintainer__ = "Eric Schles"
__maintainer_email__ = "ericschles@gmail.com"
__github_username__ = "EricSchles"

try:
    from .search import (
        SearchEngine,
        SimpleZipcode, ComprehensiveZipcode, ZipcodeTypeEnum, SORT_BY_DIST,
    )
except ImportError as e:  # pragma: no cover
    print(e)
except: # pragma: no cover
    raise
