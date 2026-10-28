# -*- coding: utf-8 -*-

"""
Build the primary-key list of 3.0: every 5-digit ZIP code we can find in free sources.

See ``README.md`` in this folder for the sources, the numbers and the open questions.
"""

from .sources import normalize_zip, is_military_zip, SOURCES
from .build import merge, write_csv, summarize, main
