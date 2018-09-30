Migrate to 0.2.x
==============================================================================


From 0.1.x
------------------------------------------------------------------------------

If you still want to stick with 0.1.x, the last 0.1.x version is 0.1.3. You can install it by ``$ pip install uszipcode==0.1.3``.

In 0.2.x a new rich info dataset is used. The API are not compatible with 0.1.x. Please read the :ref:`tutorial` to adapt new API.

There are two different database used in ``uszipcode``, ``Zipcode`` and ``SimpleZipcode``. ``Zipcode`` is the **big one with rich information** including shape polygon, popluation by age / race / time, real estate, income, employment, education info. ``SimpleZipcode`` is subset of ``Zipcode``, having **basic** postal, lat, lng, area, population, housing, and house value info.

Database file doesn't come with the installation. The **download will be automatically started if you don't have it. The database file stored at ``${HOME}/.uszipcode``.

The ``Zipcode`` database file is very big (450+MB), it may take couple of minutes to download.

If you don't need the rich info , you can choose to connect to ``SimpleZipcode`` database. The data is similar to uszipcode==0.1.3, but up-to-date and more complete.

Choose which database to use::

    >>> from uszipcode import SearchEngine
    >>> search = SearchEngine(simple_zipcode=True) # use SimpleZipcode
    # or
    >>> search = SearchEngine(simple_zipcode=False) # use Zipcode

**By default, it use** ``SimpleZipcode``

- :class:`list of info <uszipcode.model.SimpleZipcode>` with ``SimpleZipcode``.
- :class:`list of info <uszipcode.model.Zipcode>` with ``Zipcode``.
