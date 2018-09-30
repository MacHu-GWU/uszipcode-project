.. image:: https://readthedocs.org/projects/uszipcode/badge/?version=latest
    :target: https://uszipcode.readthedocs.io/?badge=latest
    :alt: Documentation Status

.. image:: https://travis-ci.org/MacHu-GWU/uszipcode-project.svg?branch=master
    :target: https://travis-ci.org/MacHu-GWU/uszipcode-project?branch=master

.. image:: https://codecov.io/gh/MacHu-GWU/uszipcode-project/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/MacHu-GWU/uszipcode-project

.. image:: https://img.shields.io/pypi/v/uszipcode.svg
    :target: https://pypi.python.org/pypi/uszipcode

.. image:: https://img.shields.io/pypi/l/uszipcode.svg
    :target: https://pypi.python.org/pypi/uszipcode

.. image:: https://img.shields.io/pypi/pyversions/uszipcode.svg
    :target: https://pypi.python.org/pypi/uszipcode

.. image:: https://img.shields.io/badge/STAR_Me_on_GitHub!--None.svg?style=social
    :target: https://github.com/MacHu-GWU/uszipcode-project

------


.. image:: https://img.shields.io/badge/Link-Document-blue.svg
      :target: https://uszipcode.readthedocs.io/index.html

.. image:: https://img.shields.io/badge/Link-API-blue.svg
      :target: https://uszipcode.readthedocs.io/py-modindex.html

.. image:: https://img.shields.io/badge/Link-Source_Code-blue.svg
      :target: https://github.com/MacHu-GWU/uszipcode-project/tree/master/uszipcode

.. image:: https://img.shields.io/badge/Link-Install-blue.svg
      :target: `install`_

.. image:: https://img.shields.io/badge/Link-GitHub-blue.svg
      :target: https://github.com/MacHu-GWU/uszipcode-project

.. image:: https://img.shields.io/badge/Link-Submit_Issue-blue.svg
      :target: https://github.com/MacHu-GWU/uszipcode-project/issues

.. image:: https://img.shields.io/badge/Link-Request_Feature-blue.svg
      :target: https://github.com/MacHu-GWU/uszipcode-project/issues

.. image:: https://img.shields.io/badge/Link-Download-blue.svg
      :target: https://pypi.org/pypi/uszipcode#files


Welcome to ``uszipcode`` Documentation
==============================================================================

**If you are on www.pypi.org or www.github.com**, this is not the complete document. Here is the `Complete Document <https://uszipcode.readthedocs.io/index.html>`_.


``uszipcode`` is the **most powerful and easy to use programmable zipcode database** in Python. It comes with a rich feature and easy-to-use zipcode search engine. And it is easy to customize the search behavior as you wish.


Data Points
------------------------------------------------------------------------------

From version 0.2.0, ``uszipcode`` use a more up-to-date database, and having a crawler running every week to collection different data points from multiple data source. And **API in 0.2.X NOT COMPATIBLE with 0.1.X**, please read `Document <https://uszipcode.readthedocs.io/index.html>`_ for more information.

**Address, Postal**

- zipcode
- zipcode_type
- major_city
- post_office_city
- common_city_list
- county
- state
- **area_code_list**

**Geography**

- lat
- lng
- timezone
- radius_in_miles
- land_area_in_sqmi
- water_area_in_sqmi
- bounds_west
- bounds_east
- bounds_north
- bounds_south
- **border polygon**

**Stats and Demographics**

- population
- population_density
- population_by_year
- population_by_age
- population_by_gender
- population_by_race
- head_of_household_by_age
- families_vs_singles
- households_with_kids
- children_by_age

**Real Estate and Housing**

- housing_units
- occupied_housing_units

- median_home_value
- median_household_income

- housing_type
- year_housing_was_built
- housing_occupancy
- vancancy_reason
- owner_occupied_home_values
- rental_properties_by_number_of_rooms

- monthly_rent_including_utilities_studio_apt
- monthly_rent_including_utilities_1_b
- monthly_rent_including_utilities_2_b
- monthly_rent_including_utilities_3plus_b

**Employment, Income, Earnings, and Work**

- employment_status
- average_household_income_over_time
- household_income
- annual_individual_earnings

- sources_of_household_income____percent_of_households_receiving_income
- sources_of_household_income____average_income_per_household_by_income_source

- household_investment_income____percent_of_households_receiving_investment_income
- household_investment_income____average_income_per_household_by_income_source

- household_retirement_income____percent_of_households_receiving_retirement_incom
- household_retirement_income____average_income_per_household_by_income_source

- source_of_earnings
- means_of_transportation_to_work_for_workers_16_and_over
- travel_time_to_work_in_minutes

**Education**

- educational_attainment_for_population_25_and_over
- school_enrollment_age_3_to_17


Example Usage
------------------------------------------------------------------------------

**NOTE**:

    ``uszipcode`` has two backend database, ``SimpleZipcode`` and ``Zipcode``. ``Zipcode`` has more info, but the database file is 450MB (takes more time to download). ``SimpleZipcode`` doesn't has all data points listed above, but the database file is smaller (9MB). By default ``uszipcode`` use ``SimpleZipcode``. You can use this code to choose to use the rich info ``Zipcode``::

        >>> from uszipcode import SearchEngine
        >>> search = SearchEngine(simple_zipcode=False)

**Examples**:

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


**Fuzzy city name and state name search** does not require developer **to know the exact spelling of the city or state**. And it is case, space insensitive, having high tolerance to typo. This is very helpful if you need to build a web app with it.

.. code-block:: python

    # Looking for Chicago and IL, but entered wrong spelling.
    >>> res = search.by_city_and_state("cicago", "il")
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


.. _install:

Install
------------------------------------------------------------------------------

``uszipcode`` is released on PyPI, so all you need is:

.. code-block:: console

    $ pip install uszipcode

To upgrade to latest version:

.. code-block:: console

    $ pip install --upgrade uszipcode
