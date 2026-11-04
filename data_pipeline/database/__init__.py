# -*- coding: utf-8 -*-

"""
Step 2 of the data pipeline: the crawler registry that builds the database.

Rows are PKs (ZIP codes), columns are ``zipcode`` plus every Field of the catalog.

- the modules of this folder are the functionality and know no data source;
- ``crawlers/`` has one module per data source;
- ``fields/`` has one module per Field.

See ``README.md`` in this folder.
"""
