# -*- coding: utf-8 -*-

"""
The one place that joins the functionality (the modules of this folder) with the
Fields (``fields/``) and the crawlers (``crawlers/``).
"""

import sys

from . import crawlers, fields
from .cli import main

sys.exit(main(sys.argv[1:], fields.FIELDS, crawlers.CRAWLERS, packages=(fields, crawlers)))
