# -*- coding: utf-8 -*-

"""
The one place that joins the functionality (the modules of this folder) with the
Fields (``fields/``, ``fields/history/``) and the crawlers (``crawlers/``).
"""

import sys

from . import crawlers, fields
from .cli import main
from .fields import history

sys.exit(main(sys.argv[1:], fields.FIELDS, crawlers.CRAWLERS, packages=(fields, history, crawlers),
              history_fields=history.HISTORY_FIELDS))
