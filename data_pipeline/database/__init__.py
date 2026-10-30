# -*- coding: utf-8 -*-

"""
Step 2 of the data pipeline: the crawler registry that builds the database.

Rows are PKs (ZIP codes), columns are ``zipcode`` plus every Field of the catalog.
Each Field is claimed by exactly one crawler; each crawler downloads its source
once and parses it offline. See ``README.md`` in this folder.
"""
