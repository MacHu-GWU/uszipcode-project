# -*- coding: utf-8 -*-

"""
The data pipeline of uszipcode 3.0: it builds the database from official U.S. sources.

This package is on its own: nothing here imports the rest of ``uszipcode``, and the
rest of ``uszipcode`` imports nothing from here. It needs Python 3.11+ and only the
standard library. Run it from a clone of the repository::

    python -m uszipcode.data check

Rows are PKs (ZIP codes), columns are ``zipcode`` plus every Field of the catalog.

- the modules of this folder are the functionality and know no data source;
- ``crawlers/`` has one module per data source;
- ``fields/`` has one module per Field;
- ``zipcode_universe/`` builds the list of PKs.

See ``README.md`` in this folder.
"""
