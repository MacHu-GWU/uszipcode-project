Migrate from 0.1.x to 0.2.x
==============================================================================

If you still want to stick with 0.1.x, the last 0.1.x version is 0.1.3. You can install it by ``$ pip install uszipcode==0.1.3``.

In 0.2.x a new rich info dataset is used. The API are not compatible with 0.1.x. Please read the :ref:`tutorial` to adapt new API.

The new database file is very big (450+MB), it doesn't come with the installation. The **download will be automatically started if you choose to query from the big database**. The database file stored at ``${HOME}/.uszipcode``.

If you don't need the bonus polygon, popluation by age / race / time, real estate, income, employment, education info, you can choose to connect to ``simple_zipcode`` database. The data is similar to uszipcode==0.1.3, but up-to-date and more complete.

**By default, it use** ``simple_zipcode``
