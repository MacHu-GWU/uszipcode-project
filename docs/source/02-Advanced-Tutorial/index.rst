.. contents::
    :class: this-will-duplicate-information-and-it-is-still-useful-here
    :depth: 1
    :local:

.. _tutorial:

Advanced Tutorial
==============================================================================


.. _basic_search:

Basic Search
------------------------------------------------------------------------------

Start the search engine, do some basic search:

    >>> from uszipcode import SearchEngine, SimpleZipcode, ComprehensiveZipcode
    >>> search = SearchEngine()
    >>> zipcode = search.by_zipcode(10030)
    >>> zipcode.zipcode # access attributes
    '10030'
    >>> zipcode.major_city
    'New York'
    >>> zipcode.state_abbr
    'NY'
    >>> zipcode.population
    26999

Zipcode support comparison and is hashable, which means you can sort, or put it in a set:

    >>> bool(SimpleZipcode(zipcode="10030"))
    True
    >>> bool(SimpleZipcode())
    False
    >>> SimpleZipcode(zipcode="10030") <= SimpleZipcode(zipcode="10031")
    True
    >>> len(set([SimpleZipcode(zipcode="10030"), SimpleZipcode(zipcode="10031")]))
    2

Context manager works too (automatically disconnect database. RECOMMENDED):

    >>> with ZipcodeSearchEngine() as search:
    ...     zipcode = search.by_zipcode(10030)

    >>> from uszipcode import SearchEngine, SimpleZipcode, ComprehensiveZipcode
    >>> search = SearchEngine()
    >>> zipcode = search.by_zipcode(10030)
    >>> zipcode.zipcode # access attributes
    '10030'
    >>> zipcode.major_city
    'New York'
    >>> zipcode.state_abbr
    'NY'
    >>> zipcode.population
    26999

Zipcode support comparison and is hashable, which means you can sort, or put it in a set:

    >>> bool(SimpleZipcode(zipcode="10030"))
    True
    >>> bool(SimpleZipcode())
    False
    >>> SimpleZipcode(zipcode="10030") <= SimpleZipcode(zipcode="10031")
    True
    >>> len(set([SimpleZipcode(zipcode="10030"), SimpleZipcode(zipcode="10031")]))
    2

Context manager works too (automatically disconnect database. RECOMMENDED):

    >>> with SearchEngine() as search:
    ...     zipcode = search.by_zipcode(10030)

    >>> from uszipcode import SearchEngine, SimpleZipcode, Zipcode
    >>> search = SearchEngine()
    >>> zipcode = search.by_zipcode(10030)
    >>> zipcode.zipcode # access attributes
    '10030'
    >>> zipcode.major_city
    'New York'
    >>> zipcode.state_abbr
    'NY'
    >>> zipcode.population
    26999

Zipcode support comparison and is hashable, which means you can sort, or put it in a set:

    >>> bool(SimpleZipcode(zipcode="10030"))
    True
    >>> bool(SimpleZipcode())
    False
    >>> SimpleZipcode(zipcode="10030") <= SimpleZipcode(zipcode="10031")
    True
    >>> len(set([SimpleZipcode(zipcode="10030"), SimpleZipcode(zipcode="10031")]))
    2

Context manager works too (automatically disconnect database. RECOMMENDED):

    >>> with ZipcodeSearchEngine() as search:
    ...     zipcode = search.by_zipcode(10030)

    >>> from uszipcode import SearchEngine, SimpleZipcode, ComprehensiveZipcode
    >>> search = SearchEngine()
    >>> zipcode = search.by_zipcode(10030)
    >>> zipcode.zipcode # access attributes
    '10030'
    >>> zipcode.major_city
    'New York'
    >>> zipcode.state_abbr
    'NY'
    >>> zipcode.population
    26999

Zipcode support comparison and is hashable, which means you can sort, or put it in a set:

    >>> bool(SimpleZipcode(zipcode="10030"))
    True
    >>> bool(SimpleZipcode())
    False
    >>> SimpleZipcode(zipcode="10030") <= SimpleZipcode(zipcode="10031")
    True
    >>> len(set([SimpleZipcode(zipcode="10030"), SimpleZipcode(zipcode="10031")]))
    2

Context manager works too (automatically disconnect database. RECOMMENDED):

    >>> with SearchEngine() as search:
    ...     zipcode = search.by_zipcode(10030)

    >>> from uszipcode import SearchEngine, SimpleZipcode, ComprehensiveZipcode
    >>> search = SearchEngine()
    >>> zipcode = search.by_zipcode(10030)
    >>> zipcode.zipcode # access attributes
    '10030'
    >>> zipcode.major_city
    'New York'
    >>> zipcode.state_abbr
    'NY'
    >>> zipcode.population
    26999

Zipcode support comparison and is hashable, which means you can sort, or put it in a set:

    >>> bool(SimpleZipcode(zipcode="10030"))
    True
    >>> bool(SimpleZipcode())
    False
    >>> SimpleZipcode(zipcode="10030") <= SimpleZipcode(zipcode="10031")
    True
    >>> len(set([SimpleZipcode(zipcode="10030"), SimpleZipcode(zipcode="10031")]))
    2

Context manager works too (automatically disconnect database. RECOMMENDED):

    >>> with SearchEngine() as search:
    ...     zipcode = search.by_zipcode(10030)

    >>> from uszipcode import SearchEngine, SimpleZipcode, Zipcode
    >>> search = SearchEngine()
    >>> zipcode = search.by_zipcode(10030)
    >>> zipcode.zipcode # access attributes
    '10030'
    >>> zipcode.major_city
    'New York'
    >>> zipcode.state_abbr
    'NY'
    >>> zipcode.population
    26999

Zipcode support comparison and is hashable, which means you can sort, or put it in a set:

    >>> bool(SimpleZipcode(zipcode="10030"))
    True
    >>> bool(SimpleZipcode())
    False
    >>> SimpleZipcode(zipcode="10030") <= SimpleZipcode(zipcode="10031")
    True
    >>> len(set([SimpleZipcode(zipcode="10030"), SimpleZipcode(zipcode="10031")]))
    2

Context manager works too (automatically disconnect database. RECOMMENDED):

    >>> with SearchEngine() as search:
    ...     zipcode = search.by_zipcode(10030)

    >>> from uszipcode import SearchEngine, SimpleZipcode, ComprehensiveZipcode
    >>> search = SearchEngine()
    >>> zipcode = search.by_zipcode(10030)
    >>> zipcode.zipcode # access attributes
    '10030'
    >>> zipcode.major_city
    'New York'
    >>> zipcode.state_abbr
    'NY'
    >>> zipcode.population
    26999

Zipcode support comparison and is hashable, which means you can sort, or put it in a set:

    >>> bool(SimpleZipcode(zipcode="10030"))
    True
    >>> bool(SimpleZipcode())
    False
    >>> SimpleZipcode(zipcode="10030") <= SimpleZipcode(zipcode="10031")
    True
    >>> len(set([SimpleZipcode(zipcode="10030"), SimpleZipcode(zipcode="10031")]))
    2

Context manager works too (automatically disconnect database. RECOMMENDED):

    >>> with ZipcodeSearchEngine() as search:
    ...     zipcode = search.by_zipcode(10030)

**Convert the object to dictionary / json is easy**:

- You can use :meth:`~uszipcode.model.SimpleZipcode.to_json(include_null=True)` method to return json encoded string.
- You can use :meth:`~uszipcode.model.SimpleZipcode.to_dict(include_null=True)` method to return dictionary data.
- You can use :meth:`~uszipcode.model.SimpleZipcode.to_OrderedDict(include_null=True)` method to return ordered dictionary data.
- You can use :meth:`~uszipcode.model.SimpleZipcode.keys()` method to return available attribute list.
- You can use :meth:`~uszipcode.model.SimpleZipcode.values()` method to return attributes' values.

By default, ``uszipcode`` **only returns Standard zipcode**, if you want to **return other zipcode type, or return all kinds of zipcode**, please see :ref:`zipcode_type`.


.. _search_way:

List of the Way you can Search
------------------------------------------------------------------------------

Here's the list of the ways you can search zipcode:

- :meth:`~uszipcode.search.SearchEngine.query`
- :meth:`~uszipcode.search.SearchEngine.by_zipcode`
- :meth:`~uszipcode.search.SearchEngine.by_city_and_state`
- :meth:`~uszipcode.search.SearchEngine.by_city`,
- :meth:`~uszipcode.search.SearchEngine.by_state`
- :meth:`~uszipcode.search.SearchEngine.by_prefix`
- :meth:`~uszipcode.search.SearchEngine.by_pattern`
- :meth:`~uszipcode.search.SearchEngine.by_population`
- :meth:`~uszipcode.search.SearchEngine.by_population_density`
- :meth:`~uszipcode.search.SearchEngine.by_land_area_in_sqmi`
- :meth:`~uszipcode.search.SearchEngine.by_water_area_in_sqmi`
- :meth:`~uszipcode.search.SearchEngine.by_housing_units`
- :meth:`~uszipcode.search.SearchEngine.by_occupied_housing_units`
- :meth:`~uszipcode.search.SearchEngine.by_median_home_value`
- :meth:`~uszipcode.search.SearchEngine.by_median_household_income`

For sorting and limit the result, you also should know about :ref:`sort` and :ref:`limit`.


.. _by_city_and_state:

Search by City and State
------------------------------------------------------------------------------
You can search **by city and state name**, **multiple results may returns**. Plus, **fuzzy name search is supported**. Which means even the inputs has spelling problem, the fuzzy matching algorithm can still find out the city and state your are looking for, no matter using 2 letter short name or full state name.

.. code-block:: python

    >>> res = search.by_city_and_state(city="cicago", state="ilinoy") # smartly guess what you are looking for
    >>> len(res) # matched 56 zipcode
    56
    >>> zipcode = res[0]
    >>> zipcode.major_city
    'Chicago'

    >>> zipcode.state_abbr
    'IL'

Short state name also works:

    >>> res = search.by_city_and_state(city="cicago", state="il") # smartly guess what you are looking for
    >>> len(res) # 56 zipcodes in Chicago
    56
    >>> zipcode = res[0]
    >>> zipcode.major_city
    'Chicago'
    >>> zipcode.state_abbr
    'IL'

You can add ``zipcode_type=ZipcodeType.PO_Box`` parameter to only include Po Box type zipcode. Or you can add ``zipcode_type=None`` to return any type of zipcode. By default, return standard type zipcode only:

    >>> res = search.by_city_and_state(city="Chicago", state="IL", zipcode_type=ZipcodeType.PO_Box)


.. _by_city:

Search by City
------------------------------------------------------------------------------
You can search zipcode by city name.

.. code-block:: python

    >>> res = search.by_city("vienna")
    >>> zipcode = res[0]
    >>> zipcode.major_city
    'Vienna'


**uszipcode also provide a internal method to help you find correct city name**::

.. code-block: python

    >>> search.find_city("phonix", bes_match=True)
    ['Phoenix']

    # Find city in kensas state, state name is also typo tolerant
    >>> search.find_city("kersen", state="kensas", best_match=False)
    ["Nickerson", ]


.. _by_state:

Search by State
------------------------------------------------------------------------------
You can search zipcode by state name.

.. code-block:: python

    >>> res = search.by_state("Rhode Island")
    >>> zipcode = res[0]
    >>> zipcode.state_abbr
    'RI'


.. _by_coordinate:

Search by Latitude and Longitude
------------------------------------------------------------------------------

You can search all zipcode with-in range of XXX miles from a coordinate. You can add ``returns=xxx`` to set maximum number of zipcode can be returned. By default, it's 5. Use ``returns=0`` to remove the limit. **The results are sorted by the distance from the center, from lowest to highest**.

.. code-block:: python

    >>> result = search.by_coordinates(39.122229, -77.133578, radius=30)
    >>> len(res) # by default 5 results returned
    5
    >>> for zipcode in result:
    ...     # do whatever you want...


    >>> result = search.by_coordinates(39.122229, -77.133578, radius=100, returns=None)
    >>> len(result) # the return limit is removed
    3531


.. _by_prefix:

Search by Zipcode Prefix
------------------------------------------------------------------------------
You can search all zipcode by its prefix:

.. code-block:: python

    >>> result = search.by_prefix("900")
    >>> for zipcode in result:
    ...     print(zipcode.zipcode)
    90001
    90002
    90003
    ...


.. _by_range:

Search by Range of XXX
------------------------------------------------------------------------------
You can search zipcode by defining the lower bound and the upper bound of any zipcode attribute.

.. code-block:: python

    >>> result = search.by_population(lower=5000, upper=10000)
    >>> for zipcode in result:
    ...     # do whatever you want...

    >>> result = search.by_population_density(lower=1000, upper=2000)
    >>> for zipcode in result:
    ...     # do whatever you want...

These attributes support range query:

- :meth:`~uszipcode.search.SearchEngine.by_population`
- :meth:`~uszipcode.search.SearchEngine.by_population_density`
- :meth:`~uszipcode.search.SearchEngine.by_land_area_in_sqmi`
- :meth:`~uszipcode.search.SearchEngine.by_water_area_in_sqmi`
- :meth:`~uszipcode.search.SearchEngine.by_housing_units`
- :meth:`~uszipcode.search.SearchEngine.by_occupied_housing_units`
- :meth:`~uszipcode.search.SearchEngine.by_median_home_value`
- :meth:`~uszipcode.search.SearchEngine.by_median_household_income`


.. _find:

Advance Search
------------------------------------------------------------------------------
In addition, above methods can mix each other to implement very advance search:

**Find most people-living zipcode in New York**

.. code-block:: python

    res = search.find(
        city="new york",
        sort_by=Zipcode.population,
        ascending=False,
    )

**Find all zipcode in California that prefix is "999"**

.. code-block:: python

    res = search.find(
        state="califor",
        prefix="95",
        sort_by=Zipcode.housing_units,
        ascending=False,
        returns=100,
    )

**Find top 10 richest zipcode near Silicon Valley**

.. code-block:: python

    # Find top 10 richest zipcode near Silicon Valley
    lat, lng = 37.391184, -122.082235
    radius = 100
    res = search.find(
        lat=lat,
        lng=lng,
        radius=radius,
        sort_by=Zipcode.median_household_income,
        ascending=False,
        returns=10,
    )


.. _custom_query:

Custom Query
------------------------------------------------------------------------------

The :class:`~uszipcode.model.Zipcode` and :class:`~uszipcode.model.SimpleZipcode` are actually sqlalchemy orm declarative base class. If you are familiar with sqlalchemy orm, you can write the query this way:

.. code-block:: python

    >>> import sqlalchemy as sa
    >>> from uszipcode import SearchEngine, SimpleZipcode
    >>> search = SearchEngine(simple_zipcode=True)
    >>> sql = sa.select(SimpleZipcode).where(SimpleZipcode.zipcode=="10001")
    >>> search.ses.scalar(stmt).one()
    SimpleZipcode(zipcode="10001", ...)


.. _zipcode_type:

Zipcode Type
------------------------------------------------------------------------------

There are four type of zipcode:

- PO Box: used only for PO Boxes at a given facility, not for any other type of delivery
- Unique: assigned to a single high-volume address
- Military: used to route mail for the U.S. military
- Standard: all other ZIP Codes.

This database doesn't have ``Military``. And only the Standard zipcode has rich info.

.. note::

    By default, ``uszipcode`` only returns Standard zipcode. If you want to return PO Box or Unique zipcode, you can specify::

        search.by_xxx(..., zipcode_type=ZipcodeTypeEnum.PO_Box)

    If you want to return all kinds of zipcode, you can specify::

        search.by_xxx(..., zipcode_type=None)


.. _sort:

Sort Result by Attribute
------------------------------------------------------------------------------
Most of built-in methods support ``sort_by``, ``ascending`` keyword (:meth:`~uszipcode.search.SearchEngine.by_zipcode` suppose to return only one result).

- :meth:`~uszipcode.search.SearchEngine.by_city_and_state`
- :meth:`~uszipcode.search.SearchEngine.by_city`
- :meth:`~uszipcode.search.SearchEngine.by_state`
- :meth:`~uszipcode.search.SearchEngine.by_prefix`
- :meth:`~uszipcode.search.SearchEngine.by_pattern`
- :meth:`~uszipcode.search.SearchEngine.by_population`
- :meth:`~uszipcode.search.SearchEngine.by_population_density`
- :meth:`~uszipcode.search.SearchEngine.by_housing_units`
- :meth:`~uszipcode.search.SearchEngine.by_occupied_housing_units`
- :meth:`~uszipcode.search.SearchEngine.by_median_home_value`
- :meth:`~uszipcode.search.SearchEngine.by_median_household_income`

- :meth:`uszipcode.search.SearchEngine.query`

Arguments:

- ``sort_by``: str in attribute name, for example ``"zipcode"``or an ORM object attribute, for example ``Zipcode.zipcode``.
- ``ascending``: bool, True means ascending, False means descending.

.. code-block:: python

    # Search zipcode that average annual income per person greater than $100,000
    >>> res = search.query(city="New York", state=="NY", sort_by=Zipcode.median_household_income, ascending=False)
    >>> for zipcode in res:
    ...     print(zipcode.median_household_income) # should be in descending order


.. _limit:

Restrict Number of Results to Return
------------------------------------------------------------------------------
Every search method support ``returns`` keyword to limit number of results to return. Zero is for unlimited. The default limit is 5.

Here's an example to find the top 10 most people zipcode, sorted by population:

.. code-block:: python

    # Find the top 10 population zipcode
    >>> res = search.by_population(upper=999999999, sort_by="population", ascending=False, returns=10)
    >>> len(res)
    10
    >>> for zipcode in res:
    ...     print(zipcode.Population) # should be in descending order
