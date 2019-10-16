.. _changelog:

Release and Version History
==============================================================================


0.2.5 (TODO)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Get lat lng and more geo info from Google Geocoding API for **Unique** and **PO Box** zipcode.
- Allow user to dump the data to any relational database easily and use self-hosted database to query.

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


0.2.4 (2019-10-16)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Now you can use ``SearchEngine(..., db_file_dir="/tmp")`` to specify where you want to put your database. By default it is ``${HOME}/.uszipcode``.

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


0.2.3 (2019-10-07)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Miscellaneous**

- move the default download dir to /tmp folder, so this database can be used in AWS Lambda.


0.2.2 (2018-10-15)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Minor Improvements**

- SearchEngine.by_zipcode has a new optional parameter ``zero_padding=True``.

**Bugfixes**

- SearchEngine.by_zipcode should returns any zipcode_type by default. (It used to only return standard zipcode)


0.2.1 (2018-09-29)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- add an alias for ``Zipcode.major_city`` attribute. Now you can access it by ``Zipcode.city``
- add a utility method ``Zipcode.glance()`` to allow user to print major attributes and values instead of all attributes.

**Minor Improvements**

- Emphasize that there are two database used, and add an instruction for how to switching between these two.


0.2.0 (2018-09-15)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- The data quality is greatly improved, now it has Address, Geography, Stats Demographics, Real Estate and Housing, Employment, Income, Earnings, and Work, and Education data. And some of them are time series.
- The query API are re-implemented on top of `sqlalchemy <https://www.sqlalchemy.org/>`_.

**Miscellaneous**

- Now there are two built-in database you can query from. One is a small one, doesn't have rich info, but it is small (10MB). Another is a big one (450MB) with all information. By default is use the small one, `simple_zipcode`. If you want to use the rich info one, you can specify: ``search = SearchEngine(simple_zipcode=False)``. And the big database will automatically downloaded to your ``$HOME/.uszipcode/`` directory.


0.1.3 (2017-12-26)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- a stable and usable version.


0.0.1 (2015-10-06)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- First release