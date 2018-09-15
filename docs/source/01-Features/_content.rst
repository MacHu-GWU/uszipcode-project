.. contents::

.. _tutorial:

5 Minutes Tutorial with Examples
==============================================================================


.. _basic_search:

Basic Search
------------------------------------------------------------------------------

Start the search engine, do some basic search::

	>>> from __future__ import print_function
	>>> from uszipcode import ZipcodeSearchEngine
	>>> search = ZipcodeSearchEngine()
	>>> zipcode = search.by_zipcode(10030)
	>>> zipcode.Zipcode # access attributes
	'10030'

	>>> zipcode.City
	'New York'

	>>> zipcode.State
	'NY'

	>>> zipcode["Population"] # index access also works too
	26999

	>>> bool(zipcode)
	True

	>>> zipcode = search.by_zipcode("9999999")
	>>> bool(zipcode)
	False


Context manager works too (automatically disconnect database. RECOMMENDED)::

	>>> with ZipcodeSearchEngine() as search:
	...     zipcode = search.by_zipcode(10030)
	...     print(zipcode) # print nicely formatted json, all available attributes are listed
	{
	    "City": "New York",
	    "Density": 96424.99999999999,
	    "HouseOfUnits": 12976,
	    "LandArea": 0.28,
	    "Latitude": 40.8173411,
	    "Longitude": -73.94332990000001,
	    "NEBoundLatitude": 40.824031899999994,
	    "NEBoundLongitude": -73.9367209,
	    "Population": 26999,
	    "SWBoundLatitude": 40.812791,
	    "SWBoungLongitude": -73.948677,
	    "State": "NY",
	    "TotalWages": 345769267.0,
	    "WaterArea": 0.0,
	    "Wealthy": 12806.743471980444,
	    "Zipcode": "10030",
	    "ZipcodeType": "Standard"
	}

There are two method you may need:

- You can use :meth:`~Zipcode.to_json()` method to return json encoded string.
- You can use :meth:`~Zipcode.to_dict()` method to return dictionary data.
- You can use :meth:`~Zipcode.to_OrderedDict()` method to return ordered dictionary data.
- You can use :meth:`~Zipcode.keys()` method to return available attribute list.
- You can use :meth:`~Zipcode.values()` method to return attributes' values.

.. _search_way:

List of the way you can search
------------------------------------------------------------------------------
Here's the list of the ways you can search zipcode:

- `by city and state <by_city_and_state_>`_
- `by city <by_city_>`_
- `by state <by_state_>`_
- `by latitude, longitude and radius <by_coordinate_>`_
- `by zipcode prefix <by_prefix_>`_
- `by estimated population <by_population_>`_
- `by estimated population density <by_density_>`_
- `by landarea <by_landarea_>`_
- `by waterarea <by_waterarea_>`_
- `by estimated total annual wage <by_total_wage_>`_
- `by estimated average total annual wage <by_wealthy_>`_
- `by estimated house of units <by_house_>`_
- `advance search search <find_>`_

You also should know `this trick <sort_>`_ to sort your results.


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

.. code-block:: python

	>>> res = search.by_city_and_state(city="cicago", state="il") # smartly guess what you are looking for
	>>> len(res) # 56 zipcodes in Chicago
	56
	>>> zipcode = res[0]
	>>> zipcode.major_city
	'Chicago'
	>>> zipcode.state_abbr
	'IL'

You can add ``zipcode_type=ZipcodeType.PO_Box`` parameter to only include Po Box type zipcode. Or you can add ``zipcode_type=None`` to return any type of zipcode. By default, return standard type zipcode only::

.. code-block:: python

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
You can search all zipcode with-in range of XXX miles to a coordinate. You can add ``returns=xxx`` to set maxiumum number of zipcode can be returned. By default, it's 5. Use ``returns=0`` to remove the limit. **The results are sorted by the distance from the center, from lowest to highest**.

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


.. _by_population:

Search by Zipcode Estimate Population
------------------------------------------------------------------------------
You can search all zipcode by defining its population lower bound or upper bound, or both:

.. code-block:: python

	>>> result = search.by_population(lower=5000, upper=10000)
	>>> for zipcode in result:
	...     # do whatever you want...


.. _by_density:

Search by Zipcode Estimate Population Density
------------------------------------------------------------------------------
You can search all zipcode by defining its population density lower bound or upper bound, or both. Density is the estimate population / total land area in square miles:

.. code-block:: python

	>>> result = search.by_population_density(lower=1000, upper=2000)
	>>> for zipcode in result:
	...     # do whatever you want...


.. _by_landarea:

Search by Landarea of Zipcode
------------------------------------------------------------------------------
You can search all zipcode by defining its Landarea lower bound or upper bound, or both:

.. code-block:: python

	>>> result = search.by_land_area_in_sqmi(lower=1000, upper=2000)
	>>> for zipcode in result:
	...     # do whatever you want...


.. _by_waterarea:

Search by Waterarea of Zipcode
------------------------------------------------------------------------------
You can search all zipcode by defining its Waterarea lower bound or upper bound, or both:

.. code-block:: python

	>>> result = search.by_water_area_in_sqmi(lower=100, upper=200)
	>>> for zipcode in result:
	...     # do whatever you want...


.. _by_house:

Search by Zipcode Estimate Total House of Units
------------------------------------------------------------------------------
You can search all zipcode by defining its total house of units lower bound or upper bound, or both:

.. code-block:: python

	>>> result = search.by_housing_units(lower=20000)
	...


.. _find:

Advance Search
------------------------------------------------------------------------------
In addition, above methods can mix each other to implement very advance search:

**Find most people-living zipcode in New York**

.. code-block:: python

	res = search.find(
	    city="new york",
	    sort_by="Population", ascending=False,
	)

**Find all zipcode in California that prefix is "999"**

.. code-block:: python

	res = search.find(
	    state="califor",
	    prefix="95",
	    sort_by="HouseOfUnits", ascending=False,
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
        sort_by="Wealthy", ascending=False,
        returns=10,
    )

**Find zipcode that average personal annual income greater than $100,000 near Silicon Valley, order by distance**

.. code-block:: python

	lat, lng = 37.391184, -122.082235
	radius = 100
	res = search.find(
	    lat=lat,
	    lng=lng,
	    radius=radius,
	    wealthy_lower=60000,
	    sort_by="Dist",
	    ascending=True,
	    returns=0,
	)


.. _custom_query:

Custom Query
------------------------------------------------------------------------------

The :class:`~uszipcode.model.Zipcode` and :class:`~uszipcode.model.SimpleZipcode` are actually sqlalchemy orm declarative base class. If you are familiar with sqlalchemy orm, you can write the query this way:

.. code-block:: python

    >>> from uszipcode import SearchEngine, SimpleZipcode
    >>> search = SearchEngine(simple_zipcode=True)
    >>> search.ses.query(SimpleZipcode).filter(SimpleZipcode.zipcode=="10001").one()
    SimpleZipcode(zipcode="10001", ...)


.. _sort:

Sort Result
------------------------------------------------------------------------------
- :meth:`~uszipcode.search.SearchEngine.by_city_and_state`
- :meth:`~uszipcode.search.SearchEngine.by_city`, ``by_state``, ``by_prefix``, ``by_population``, ``by_population_density``, ``by_totalwages``, ``by_wealthy``, ``by_housing_units`` methods all support ``sort_by``, ``ascending`` keyword.

- ``sort_by``: attribute name(s), case insensitive. Accepts an attribute name or a list for a nested sort. By default ordered by ``Zipcode``. All valid attribute name is :class:`listed here <uszipcode.searchengine.Zipcode>`
- ``ascending``: boolean or list, default ``True``, sort ascending vs. descending. Specify list for multiple sort orders

.. code-block:: python

	# Search zipcode that average annual income per person greater than $100,000
	>>> res = search.by_wealthy(lower=100000, sort_by="Wealthy", ascending=True)
	>>> for zipcode in res:
	...     print(zipcode.Wealthy) # should be in ascending order


.. _limit:

Restrict number of results to return
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

.. include:: about.rst