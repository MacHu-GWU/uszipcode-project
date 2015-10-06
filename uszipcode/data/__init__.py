#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This package using the integrated data made by Sanhe Hu, Data Scientist in 
WeatherBug Home, which includes:

- 2012-01-22 federal governmanet zipcode data from 
  http://federalgovernmentzipcodes.us/
- 2010 zcta2010 population, wage, houseunit, land, water area data from
  from http://proximityone.com/cen2010_zcta_dp.htm
- 2015-10-01 geometry google map geocoding data from http://maps.google.com
"""

import site
import os

DB_FILE = os.path.join(
    site.getsitepackages()[1], "uszipcode", "data", "zipcode.sqlite3")

STATE_ABBR_SHORT_TO_LONG = { # state short time and long name mapping
"AK" : "Alaska",
"AL" : "Alabama",
"AR" : "Arkansas",
"AZ" : "Arizona",
"CA" : "California",
"CO" : "Colorado",
"CT" : "Connecticut",
"DC" : "District of Columbia",
"DE" : "Delaware",
"FL" : "Florida",
"GA" : "Georgia",
"GU" : "Guam",
"HI" : "Hawaii",
"IA" : "Iowa",
"ID" : "Idaho",
"IL" : "Illinois",
"IN" : "Indiana",
"KS" : "Kansas",
"KY" : "Kentucky",
"LA" : "Louisiana",
"MA" : "Massachusetts",
"MD" : "Maryland",
"ME" : "Maine",
"MI" : "Michigan",
"MN" : "Minnesota",
"MO" : "Missouri",
"MS" : "Mississippi",
"MT" : "Montana",
"NC" : "North Carolina",
"ND" : "North Dakota",
"NE" : "Nebraska",
"NH" : "New Hampshire",
"NJ" : "New Jersey",
"NM" : "New Mexico",
"NV" : "Nevada",
"NY" : "New York",
"OH" : "Ohio",
"OK" : "Oklahoma",
"OR" : "Oregon",
"PA" : "Pennsylvania",
"PR" : "Puerto Rico",
"RI" : "Rhode Island",
"SC" : "South Carolina",
"SD" : "South Dakota",
"TN" : "Tennessee",
"TX" : "Texas",
"UT" : "Utah",
"VA" : "Virginia",
"VI" : "Virgin Islands",
"VT" : "Vermont",
"WA" : "Washington",
"WI" : "Wisconsin",
"WV" : "West Virginia",
"WY" : "Wyoming",
}

STATE_ABBR_LONG_TO_SHORT = dict()
for k, v in STATE_ABBR_SHORT_TO_LONG.items():
    STATE_ABBR_LONG_TO_SHORT[v.lower()] = k