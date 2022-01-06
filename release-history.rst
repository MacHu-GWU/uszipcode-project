.. _release_history:

Release and Version History
==============================================================================


1.0.2 (TODO)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Make Census 2020 data generally available for all zipcode.

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


1.0.1 (2022-01-05)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Drop Python2.7 support, now it is Python3.6+ only.
- Add Census 2020 data to the database for demographic statistics over time data points.

**Minor Improvements**

- Fully adopt type hint.
- Update docs and theme.

**Bugfixes**

- Fixed some zipcode attribute name typo.

**Miscellaneous**

- Update PyPI classifiers to reflect supported Python versions (3.6 through 3.9)
- Move CI to GitHub action.


0.2.6 (2021-06-07)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Features and Improvements**

- Allow developer to use different download url in ``SearchEngine(..., download_url="your-own-download-url")``. So developer can upload the db file to a private file host server.
- Allow developer to use different database backend like mysql, postgres, oracle, mssql in ``SearchEngine(..., engine=custome_sqlachemy_engine)``. So developer can dump the sqlite to csv and load it to any database you want to use.

**Minor Improvements**

- rehost the database file on GitHub

**Bugfixes**

**Miscellaneous**

- Drop support < Python3.6, only support 3.6+


0.2.5 (2021-04-20)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- fix compability issue with sqlachemy>=1.4.X


0.2.4 (2019-10-16)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Now you can use ``SearchEngine(..., db_file_dir="/tmp")`` to specify where you want to put your database. By default it is ``${HOME}/.uszipcode``.

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