.. image:: https://travis-ci.org/MacHu-GWU/uszipcode-project.svg?branch=master

.. image:: https://img.shields.io/pypi/v/uszipcode.svg

.. image:: https://img.shields.io/pypi/l/uszipcode.svg

.. image:: https://img.shields.io/pypi/pyversions/uszipcode.svg


Welcome to uszipcode Documentation
==================================
``uszipcode`` is the **most powerful and easy to use programmable zipcode database, and also a searchengine** in Python. Besides geometry data (also boundary info), several useful census data points are also served: `population`, `population density`, `total wage`, `average annual wage`, `house of units`, `land area`, `water area`. The geometry and geocoding data I am using is from google map API on Mar 2016. `To know more about the data, click here <http://pythonhosted.org/uszipcode/uszipcode/data/__init__.html#module-uszipcode.data>`_. Another `popular zipcode Python extension <https://pypi.python.org/pypi/zipcode>`_ has lat, lng accuracy issue, which doesn't give me reliable results of searching by coordinate and radius.


**Quick Links**
-------------------------------------------------------------------------------
- `GitHub Homepage <https://github.com/MacHu-GWU/uszipcode-project>`_
- `Online Documentation <http://pythonhosted.org/uszipcode>`_
- `PyPI download <https://pypi.python.org/pypi/uszipcode>`_
- `Install <install_>`_
- `Issue submit and feature request <https://github.com/MacHu-GWU/uszipcode-project/issues>`_
- `API reference and source code <http://pythonhosted.org/uszipcode/uszipcode/searchengine.html#uszipcode.searchengine.ZipcodeSearchEngine>`_


**Highlight**:

- `Rich information <http://pythonhosted.org/uszipcode/uszipcode/searchengine.html#uszipcode.searchengine.Zipcode>`_ of zipcode is available.

.. code-block:: python

	>>> from uszipcode import ZipcodeSearchEngine
	>>> search = ZipcodeSearchEngine()
	>>> zipcode = search.by_zipcode("10001")
	>>> print(zipcode)
	{
	    "City": "New York", 
	    "Density": 34035.48387096774, 
	    "HouseOfUnits": 12476, 
	    "LandArea": 0.62, 
	    "Latitude": 40.75368539999999, 
	    "Longitude": -73.9991637, 
	    "NEBoundLatitude": 40.8282129, 
	    "NEBoundLongitude": -73.9321059, 
	    "Population": 21102, 
	    "SWBoundLatitude": 40.743451, 
	    "SWBoungLongitude": -74.00794499999998, 
	    "State": "NY", 
	    "TotalWages": 1031960117.0, 
	    "WaterArea": 0.0, 
	    "Wealthy": 48903.42702113544, 
	    "Zipcode": "10001", 
	    "ZipcodeType": "Standard"
	}

- `Rich search methods <http://pythonhosted.org/uszipcode/index.html#list-of-the-way-you-can-search>`_ are provided for getting zipcode in the way you want.

.. code-block:: python

	# Search zipcode within 30 miles, ordered from closest to farthest
	>>> res = search.by_coordinate(39.122229, -77.133578, radius=30, returns=5)
	>>> len(res) # by default 5 results returned
	5
	>>> for zipcode in res:
	...     # do whatever you want...

	# Find top 10 population zipcode
	>>> res = search.by_population(lower=0, upper=999999999, 
	... sort_by="Population", ascending=False, returns=10)

	# Find top 10 largest land area zipcode
	>>> res = search.by_landarea(lower=0, upper=999999999, 
	... sort_by="LandArea", ascending=False, returns=10)

	# Find top 10 most wealthy zipcode in new york
	>>> res = search.find(city="newyork", wealthy_lower=100000, 
	... sort_by="Wealthy", returns=10) # at least $100,000 annual income

- `Fuzzy city name and state name search <http://pythonhosted.org/uszipcode/index.html#search-by-city-and-state>`_ **enables case, space insensitive, typo tolerant input**. **You don't have to know the correct spelling of the city or state**. This is very helpful if you need to build a web app with it.

.. code-block:: python

	# Looking for Chicago and IL, but entered wrong spelling.
	>>> res = search.by_city_and_state("cicago", "il")
	>>> len(res) # 56 zipcodes in Chicago
	56
	>>> zipcode = res[0]
	>>> zipcode.City
	'Chicago'
	>>> zipcode.State
	'IL'

- You can easily `sort your results <http://pythonhosted.org/uszipcode/index.html#sortby-descending-and-returns-keyword>`_ by `population`, `area`, `wealthy` and etc...

.. code-block:: python

	# Find top 10 population zipcode
	>>> res = search.by_population(lower=0, upper=999999999, 
	... sort_by="Population", ascending=False, returns=10)
	>>> for zipcode in res:
	...     # do whatever you want...

- Easy export to csv. Result set can be easily export to csv.

.. code-block:: python

	# Find all zipcode in new york
	>>> res = search.by_city(city="New York", returns=0)
	>>> search.export_to_csv(res, "result.csv")


.. _install:

Install
-------------------------------------------------------------------------------

``uszipcode`` is released on PyPI, so all you need is:

.. code-block:: console

	$ pip install uszipcode

To upgrade to latest version:

.. code-block:: console

	$ pip install --upgrade uszipcode