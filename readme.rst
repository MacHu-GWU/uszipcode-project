Welcome to the uszipcode Documentation
====================================================================================================

``uszipcode`` is the most powerful and easy to use zipcode information searchengine in Python. Besides geometry data (also boundary info), several useful census data points are also served: `population`, `population density`, `total wage`, `average annual wage`, `house of units`, `land area`, `water area`. The geometry and geocoding data I am using is from google map API on Oct 2015. To know more about the data, `click here <http://www.wbh-doc.com.s3.amazonaws.com/uszipcode/uszipcode/data/__init__.html#module-uszipcode.data>`_. `Another pupolar zipcode Python extension <https://pypi.python.org/pypi/zipcode>`_ has lat, lng accuracy issue, which doesn't give me reliable results of searching by coordinate and radius.

**Highlight**:

1. `Rich methods <http://www.wbh-doc.com.s3.amazonaws.com/uszipcode/index.html#list-of-the-way-you-can-search>`_ are provided for getting zipcode anyway you want. 
2. `Fuzzy city name and state name <http://www.wbh-doc.com.s3.amazonaws.com/uszipcode/index.html#search-by-city-and-state>`_ allows you to search **WITHOUT using exactly accurate input**. **This is very helpful if you need to build a web app with it**.
3. You can easily `sort your results <http://www.wbh-doc.com.s3.amazonaws.com/uszipcode/index.html#sortby-descending-and-returns-keyword>`_ by `population`, `area`, `wealthy` and etc...

**Quick links**:

- `Home page <https://github.com/MacHu-GWU/uszipcode-project>`_
- `Online Documentation <http://www.wbh-doc.com.s3.amazonaws.com/uszipcode/index.html>`_
- `PyPI download <https://pypi.python.org/pypi/uszipcode>`_
- `Install <install_>`_
- `Issue submit and feature request <https://github.com/MacHu-GWU/uszipcode-project/issues>`_
- `API reference and source code <http://www.wbh-doc.com.s3.amazonaws.com/uszipcode/uszipcode/searchengine.html#uszipcode.searchengine.ZipcodeSearchEngine>`_

Now let's see some real magic!


5 minutes tutorial with examples
====================================================================================================


.. _basic_search:

Basic Search
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Context manager works too (to keep connection safe, RECOMMENDED)::

	>>> with ZipcodeSearchEngine() as search:
	... 	zipcode = search.by_zipcode(10030)
	... 	print(zipcode) # print nicely formatted json, all available attributes are listed
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

For all available zipcode attributes, `click here <file:///C:/Users/shu/Documents/PythonWorkSpace/py3/py33_projects/uszipcode-project/build/html/uszipcode/searchengine.html#uszipcode.searchengine.Zipcode>`_.

There are two method you may need:
    
1. You can use ``to_json()`` method to return json encoded string.
2. You can use ``to_dict()`` method to return dictionary data.


.. _search_way:

List of the way you can search
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here's the list of the ways you can search zipcode:

- `by city and state <by_city_and_state_>`_
- `by latitude, longitude and radius <by_coordinate_>`_
- `by zipcode prefix <by_prefix_>`_
- `by estimated population <by_population_>`_
- `by estimated population density <by_density_>`_
- `by estimated total annual wage <by_total_wage_>`_
- `by estimated average total annual wage <by_wealthy_>`_
- `by estimated house of units <by_house_>`_

You also should know `this trick <keyword_>`_ to sort your results.


.. _by_city_and_state:

Search by City and State
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can search **by city and state name**, **multiple results may returns**. Plus, **fuzzy name search is supported**. Which means even the inputs has spelling problem, the fuzzy matching algorithm can still find out the city and state your are looking for, no matter using 2 letter short name or full state name.

.. code-block:: python

	>>> res = search.by_city_and_state("cicago", "ilinoy") # smartly guess what you are looking for
	>>> len(res) # matched 56 zipcode
	56
	>>> zipcode = res[0]
	>>> zipcode.City
	'Chicago'

	>>> zipcode.State
	'IL'

Short state name also works:

.. code-block:: python

	>>> res = search.by_city_and_state("cicago", "il") # smartly guess what you are looking for
	>>> len(res)
	56
	>>> zipcode = res[0]
	>>> zipcode.City
	'Chicago'

	>>> zipcode.State
	'IL'

You can add ``standard_only=False`` parameter to enable returning Po Box type zipcode. By default, return standard type zipcode only::

	>>> res = search.by_city_and_state("Chicago", "IL", standard_only=False)


.. _by_coordinate:

Search by Latitude and Longitude
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can search all zipcode with-in range of XXX miles to a coordinate. You can add ``returns=xxx`` to set maxiumum number of zipcode can be returned. By default, it's 5. Use ``returns=0`` to remove the limit. **The results are sorted by the distance from the center, from lowest to highest**.

.. code-block:: python

	>>> res = search.by_coordinate(39.122229, -77.133578, radius=30)
	>>> len(res) # by default 5 results returned
	5
	>>> for zipcode in res:
	...		# do whatever you want...


	>>> res = search.by_coordinate(39.122229, -77.133578, radius=100, returns=0)
	>>> len(res) # the return limit is removed
	3531


.. _by_prefix:

Search by Zipcode Prefix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can search all zipcode by its prefix:

.. code-block:: python

	>>> res = search.by_prefix("900")
	>>> for zipcode in res:
	... 	print(zipcode.Zipcode)
	90001
	90002
	90003
	...

.. _by_population:

Search by Zipcode Estimate Population
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can search all zipcode by defining its population lower bound or upper bound, or both:

.. code-block:: python

	>>> res = search.by_population(lower=5000, upper=10000)
	>>> for zipcode in res:
	... 	# do whatever you want...


.. _by_density:

Search by Zipcode Estimate Population Density
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can search all zipcode by defining its population density lower bound or upper bound, or both. Density is the estimate population / total land area in square miles:

.. code-block:: python

	>>> res = search.by_density(lower=1000, upper=2000)
	>>> for zipcode in res:
	... 	# do whatever you want...


.. _by_total_wage:

Search by Zipcode Estimate Annual Total Wage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can search all zipcode by defining its annual total wage lower bound or upper bound, or both:

.. code-block:: python

	>>> res = search.by_totalwages(lower=1000**3)
	>>> for zipcode in res:
	... 	# do whatever you want...


.. _by_wealthy:

Search by Zipcode Estimate Average Annual Total Wage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can search all zipcode by defining its average annual total wage lower bound or upper bound, or both:

.. code-block:: python

	>>> res = search.by_wealthy(lower=100000)
	>>> for zipcode in res:
	... 	# do whatever you want...


.. _by_house:

Search by Zipcode Estimate Total House of Units
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can search all zipcode by defining its total house of units lower bound or upper bound, or both:

.. code-block:: python

	>>> res = search.by_house(lower=20000)
	>>> for zipcode in res:
	... 	# do whatever you want...


.. _keyword:

Sortby, Descending and Returns Keyword
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``by_prefix``, ``by_population``, ``by_density``, ``by_totalwages``, ``by_wealthy``, ``by_house`` methods support ``sortby``, ``descending`` and ``returns`` keyword.

- ``sortby``: string, default ``"Zipcode"``,the order of attributes that query results been returned
- ``descending``: boolean, default False, is in descending order
- ``returns``: maxiumum number of zipcode can be returned, use 0 for unlimited

Here's an example to find the top 100 richest zipcode, sorted by average annual wage:

.. code-block:: python

	>>> res = search.by_wealthy(lower=100000, sortby="Wealthy", descending=True, returns=100) 
	>>> for zipcode in res:
	... 	# do whatever you want...

.. _install:

Install
----------------------------------------------------------------------------------------------------

``uszipcode`` is released on PyPI, so all you need is:

.. code-block:: console

	$ pip install uszipcode

To upgrade to latest version:

.. code-block:: console
	
	$ pip install --upgrade uszipcode