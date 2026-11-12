# -*- coding: utf-8 -*-

"""
``county_list``. Claimed by ``zip-basics``.

Every county of the ZIP as JSON text: an array with one object per county, the main
county first (``county`` and ``county_fips`` are its first element). The keys of an
object:

- ``county_fips``, ``county``, ``state``: the code of the county, and its name and
  state in the Census Gazetteer (a ZIP can cross a state line);
- ``res_ratio``, ``bus_ratio``, ``oth_ratio``, ``tot_ratio``: the share of the
  ZIP's residential, business, other and all addresses that lie in this county, as
  HUD gives them. Each of the four adds up to 1 over the counties of a ZIP that has
  such addresses.

A ZIP that HUD does not list has no value.
"""

from ..core import Field, first_value

ONE = ('[{"county_fips":"11001","county":"District of Columbia","state":"DC",'
       '"res_ratio":1,"bus_ratio":1,"oth_ratio":1,"tot_ratio":1}]')

FIELDS = (
    Field(
        name="county_list",
        dtype=str,
        description=("Every county of the ZIP, the main county first: a JSON array of objects with county_fips, "
                     "county, state and res_ratio, bus_ratio, oth_ratio, tot_ratio, the share of the ZIP's "
                     "residential, business, other and all addresses in that county (HUD-USPS crosswalk)"),
        unit="JSON",
        extract=first_value("hud_counties"),
        examples=(({"hud_counties": ONE}, ONE), ({"hud_counties": None}, None), ({}, None)),
    ),
)
