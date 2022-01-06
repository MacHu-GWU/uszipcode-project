.. image:: https://github.com/MacHu-GWU/uszipcode-project/workflows/CI/badge.svg
    :target: https://github.com/MacHu-GWU/uszipcode-project/actions?query=workflow:CI

.. image:: https://codecov.io/gh/MacHu-GWU/uszipcode-project/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/MacHu-GWU/uszipcode-project

.. image:: https://readthedocs.org/projects/uszipcode/badge/?version=latest
    :target: https://uszipcode.readthedocs.io/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/uszipcode.svg
    :target: https://pypi.python.org/pypi/uszipcode

.. image:: https://img.shields.io/pypi/l/uszipcode.svg
    :target: https://pypi.python.org/pypi/uszipcode

.. image:: https://img.shields.io/pypi/pyversions/uszipcode.svg
    :target: https://pypi.python.org/pypi/uszipcode

.. image:: https://img.shields.io/pypi/dm/uszipcode
    :target: https://pypi.python.org/pypi/uszipcode

.. image:: https://img.shields.io/badge/STAR_Me_on_GitHub!--None.svg?style=social
    :target: https://github.com/MacHu-GWU/uszipcode-project

------

.. image:: https://img.shields.io/badge/Link-Document-blue.svg
    :target: https://uszipcode.readthedocs.io/index.html

.. image:: https://img.shields.io/badge/Link-API-blue.svg
    :target: https://uszipcode.readthedocs.io/py-modindex.html

.. image:: https://img.shields.io/badge/Link-Source_Code-blue.svg
    :target: https://uszipcode.readthedocs.io/py-modindex.html

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

.. contents::
    :class: this-will-duplicate-information-and-it-is-still-useful-here
    :depth: 1
    :local:

**If you are on www.pypi.org or www.github.com**, this is not the complete document. Here is the `Complete Document <https://uszipcode.readthedocs.io/index.html>`_.

**If you are looking for technical support**, click the badge below to join this gitter chat room and ask question to the author.

.. image:: https://img.shields.io/badge/Chat-Tech_Support-_.svg
      :target: https://gitter.im/MacHu-GWU-Python-Library-Technical-Support/community

``uszipcode`` is the **most powerful and easy to use programmable zipcode database** in Python. It comes with a rich feature and easy-to-use zipcode search engine. And it is easy to customize the search behavior as you wish.


About the Data
------------------------------------------------------------------------------

**Disclaimer**

I started from a academic research project for personal use. I don't promise for data accuracy, please use with your own risk.

**Where the data comes from?**

The data is crawled from data.census.gov. There's data tool allows you to explore 1300+ data points of a zipcode. You can play it yourself with this link https://data.census.gov/cedsci/table?q=94103.

**Is this data set Up-to-Date?**

Even the data.census.gov use different source for different data fields. For example, the latest general population / income / education data by zipcode are still from Census2010. But population over time data are based from IRS until FY 2018.

In general, static statistic data are from Census 2010. Demographic statistics over time has data utill 2020.

**How many Zipcode in this Database**

There are 42,724 zipcodes in this database. There are four different type zipcode:

- STANDARD: most common zipcode
- PO Box: for post office
- UNIQUE: special location, usually a single building
- MILITARY: military location

Number of zipcodes for each type::

    +--------------+-------+------------+
    | zipcode_type | count | percentage |
    +--------------+-------+------------+
    |   STANDARD   | 30001 |   70.22    |
    |    PO BOX    |  9397 |   21.99    |
    |    UNIQUE    |  2539 |    5.94    |
    |   MILITARY   |  787  |    1.84    |
    +--------------+-------+------------+

**I found a Great data source, how to contribute?**

You can open an `Issue <https://github.com/MacHu-GWU/uszipcode-project/issues/new?assignees=&labels=enhancement&template=i-found-a-data-source.md&title=I+found+a+data+source>`_ and leave the URL of the data source, brief description about the dataset.


The Data point
------------------------------------------------------------------------------

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
- vacancy_reason
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


.. _install:

Install
------------------------------------------------------------------------------

``uszipcode`` is released on PyPI, so all you need is:

.. code-block:: console

    $ pip install uszipcode

To upgrade to latest version:

.. code-block:: console

    $ pip install --upgrade uszipcode
