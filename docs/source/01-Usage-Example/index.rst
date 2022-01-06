.. _usage:

Usage Example
==============================================================================

.. contents::
    :class: this-will-duplicate-information-and-it-is-still-useful-here
    :depth: 1
    :local:

Get Zipcode Statistics and Demographic Data
------------------------------------------------------------------------------

.. code-block:: python

    from uszipcode import SearchEngine

    sr = SearchEngine()
    z = sr.by_zipcode("10001")
    print(z)

    z = sr.by_zipcode(10001)
    print(z)

Simple vs Comprehensive Zipcode Database
------------------------------------------------------------------------------
``uszipcode`` has two backend database, ``SimpleZipcode`` and ``ComprehensiveZipcode``. ``ComprehensiveZipcode`` has more data points, but the database file is 450MB (takes more time to download). ``SimpleZipcode`` doesn't has all data points listed above, but the database file is smaller (10MB). By default ``uszipcode`` use ``SimpleZipcode``. You can use this code to choose to use the rich info ``Zipcode``:

.. code-block:: python

    >>> from uszipcode import SearchEngine

    # use simple zipcode
    >>> search = SearchEngine(
    ... simple_or_comprehensive=SearchEngine.SimpleOrComprehensiveArgEnum.simple
    )
    # use comprehensive zipcode
    >>> search = SearchEngine(
    ... simple_or_comprehensive=SearchEngine.SimpleOrComprehensiveArgEnum.comprehensive
    )

Change the Default Database File location
------------------------------------------------------------------------------
``uszipcode`` allows developer to choose which directory you want to use to download the database file**. By default, it is ``$HOME/.uszipcode``, but you can easily change it.:

.. code-block:: python

    >>> search = SearchEngine(db_file_path="/tmp/simple_db.sqlite")

For example, AWS Lambda doesn't allow to download file to $HOME directory, but allows to download to ``/tmp`` folder.

Change the Default Download URL
------------------------------------------------------------------------------
By default, the database file are hosted on GitHub. But you can host it elsewhere like your private storage.

.. code-block:: python

    >>> search = SearchEngine(download_url="https://your-private-storage.sqlite")

SearchEngine Examples
------------------------------------------------------------------------------

.. code-block:: python

    >>> from uszipcode import SearchEngine
    >>> search = SearchEngine(simple_zipcode=True) # set simple_zipcode=False to use rich info database
    >>> zipcode = search.by_zipcode("10001")
    >>> zipcode
    SimpleZipcode(zipcode=u'10001', zipcode_type=u'Standard', major_city=u'New York', post_office_city=u'New York, NY', common_city_list=[u'New York'], county=u'New York County', state=u'NY', lat=40.75, lng=-73.99, timezone=u'Eastern', radius_in_miles=0.9090909090909091, area_code_list=[u'718', u'917', u'347', u'646'], population=21102, population_density=33959.0, land_area_in_sqmi=0.62, water_area_in_sqmi=0.0, housing_units=12476, occupied_housing_units=11031, median_home_value=650200, median_household_income=81671, bounds_west=-74.008621, bounds_east=-73.984076, bounds_north=40.759731, bounds_south=40.743451)

    >>> zipcode.values() # to list
    [u'10001', u'Standard', u'New York', u'New York, NY', [u'New York'], u'New York County', u'NY', 40.75, -73.99, u'Eastern', 0.9090909090909091, [u'718', u'917', u'347', u'646'], 21102, 33959.0, 0.62, 0.0, 12476, 11031, 650200, 81671, -74.008621, -73.984076, 40.759731, 40.743451]

    >>> zipcode.to_dict() # to dict
    {'housing_units': 12476, 'post_office_city': u'New York, NY', 'bounds_east': -73.984076, 'county': u'New York County', 'population_density': 33959.0, 'radius_in_miles': 0.9090909090909091, 'timezone': u'Eastern', 'lng': -73.99, 'common_city_list': [u'New York'], 'zipcode_type': u'Standard', 'zipcode': u'10001', 'state': u'NY', 'major_city': u'New York', 'population': 21102, 'bounds_west': -74.008621, 'land_area_in_sqmi': 0.62, 'lat': 40.75, 'median_household_income': 81671, 'occupied_housing_units': 11031, 'bounds_north': 40.759731, 'bounds_south': 40.743451, 'area_code_list': [u'718', u'917', u'347', u'646'], 'median_home_value': 650200, 'water_area_in_sqmi': 0.0}

    >>> zipcode.to_json() # to json
    {
        "zipcode": "10001",
        "zipcode_type": "Standard",
        "major_city": "New York",
        "post_office_city": "New York, NY",
        "common_city_list": [
            "New York"
        ],
        "county": "New York County",
        "state": "NY",
        "lat": 40.75,
        "lng": -73.99,
        "timezone": "Eastern",
        "radius_in_miles": 0.9090909090909091,
        "area_code_list": [
            "718",
            "917",
            "347",
            "646"
        ],
        "population": 21102,
        "population_density": 33959.0,
        "land_area_in_sqmi": 0.62,
        "water_area_in_sqmi": 0.0,
        "housing_units": 12476,
        "occupied_housing_units": 11031,
        "median_home_value": 650200,
        "median_household_income": 81671,
        "bounds_west": -74.008621,
        "bounds_east": -73.984076,
        "bounds_north": 40.759731,
        "bounds_south": 40.743451
    }

Rich search methods are provided for getting zipcode in the way you want.

.. code-block:: python

    >>> from uszipcode import Zipcode
    # Search zipcode within 30 miles, ordered from closest to farthest
    >>> result = search.by_coordinates(39.122229, -77.133578, radius=30, returns=5)
    >>> len(res) # by default 5 results returned
    5
    >>> for zipcode in result:
    ...     # do whatever you want...

    # Find top 10 population zipcode
    >>> result = search.by_population(lower=0, upper=999999999,
    ... sort_by=Zipcode.population, ascending=False, returns=10)

    # Find top 10 largest land area zipcode
    >>> res = search.by_landarea(lower=0, upper=999999999,
    ... sort_by=Zipcode.land_area_in_sqmi, ascending=False, returns=10)

Zipcode Type
------------------------------------------------------------------------------
By default, most of zipcode query only returns STANDARD zipcode. If you want all zipcode or specific type of zipcode, you can do:

.. code-block:: python

    >>> from uszipcode import ZipcodeTypeEnum

    # return all zipcode type
    >>> res = sr.by_coordinates(..., zipcode_type=None)

    # return only PO box type
    >>> res = sr.by_coordinates(..., zipcode_type=ZipcodeTypeEnum.PO_Box)

**Fuzzy city name and state name search** does not require developer **to know the exact spelling of the city or state**. And it is case, space insensitive, having high tolerance to typo. This is very helpful if you need to build a web app with it.

.. code-block:: python

    # Looking for Chicago and IL, but entered wrong spelling.
    >>> res = search.by_city_and_state("cicago", "il", returns=999) # only returns first 999 results
    >>> len(res) # 56 zipcodes in Chicago
    56
    >>> zipcode = res[0]
    >>> zipcode.major_city
    'Chicago'
    >>> zipcode.state_abbr
    'IL'

You can **easily sort your results** by any field, or distance from a coordinates if you query by location.

.. code-block:: python

    # Find top 10 population zipcode
    >>> res = search.by_population(lower=0, upper=999999999,
    ... sort_by=Zipcode.population, ascending=False, returns=10)
    >>> for zipcode in res:
    ...     # do whatever you want...


Deploy uszipcode as a Web Service
------------------------------------------------------------------------------
I collect lots of feedback from organization user that people want to host the database file privately. And people may love to use different rdbms backend like mysql or psql. From ``0.2.6``, this is easy.


**Host the database file privately**

1. download db file from https://github.com/MacHu-GWU/uszipcode-project/releases/download/1.0.1.db/simple_db.sqlite
2. upload it to your private storage.
3. use ``download_url`` parameter:

.. code-block:: python

    search = SearchEngine(download_url="https://your-private-store.sqlite")

**Use different RDBMS backend**:

1. Let's use MySQL as example.
2. Download db file.
3. use `DBeaver <https://dbeaver.io/>`_ to connect to both sqlite and mysql.
4. dump sqlite as csv and load it to mysql.
5. use ``engine`` parameter

.. code-block:: python

    import sqlalchemy_mate as sam

    engine = sam.EngineCreator(username, password, host, port, database)..create_postgresql_pg8000()
    search = SearchEngine(engine=engine)

**Deploy uszipcode as Web API**:

1. Use a VM like EC2 machine, and deploy a web api server with the machine.
2. (RECOMMEND) Dump the sqlite database to any relational database like Postgres, MySQL, and inject the database connection info in your application server.
