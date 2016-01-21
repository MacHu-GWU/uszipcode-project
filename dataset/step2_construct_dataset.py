#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script is to construct a zipcode sqlite database for uszipcode extension.
"""

from __future__ import print_function
from pprint import pprint as ppt
from sqlite4dummy import *
import pandas as pd
import json

def titleize(text):
    """Capitalizes all the words and replaces some characters in the string 
    to create a nicer looking title.
    """
    if len(text) == 0: # if empty string, return it
        return text
    else:
        text = text.lower() # lower all char
        # delete redundant empty space 
        chunks = [chunk[0].upper() + chunk[1:] for chunk in text.split(" ") if len(chunk) >= 1]
        return " ".join(chunks)
 
engine = Sqlite3Engine("geocode.sqlite3")
metadata = MetaData()
metadata.reflect(engine)
geo_result = metadata.get_table("geo_result")
 
# --- google geocoding result ---
geocode_data = dict()
for zipcode, json_text in engine.select(Select(geo_result.all)):
    try:
        zipcode = json.loads(zipcode)
        json_dict = json.loads(json_text)
        northeastbound_lat = json_dict["geometry"]["bounds"]["northeast"]["lat"]
        northeastbound_lng = json_dict["geometry"]["bounds"]["northeast"]["lng"]
        southwestbound_lat = json_dict["geometry"]["bounds"]["southwest"]["lat"]
        southwestbound_lng = json_dict["geometry"]["bounds"]["southwest"]["lng"]
        lat_google = json_dict["geometry"]["location"]["lat"]
        lng_google = json_dict["geometry"]["location"]["lng"]
        geocode_data[zipcode] = [northeastbound_lat, northeastbound_lng, 
                            southwestbound_lat, southwestbound_lng, 
                            lat_google, lng_google]
    except Exception as e:
        pass
print("Got %s zipcode google geocoded." % len(geocode_data))

# --- primary zipcode data ---
primary_zipcode_data = dict()
df = pd.read_csv("free-zipcode-database-Primary.csv", dtype={"Zipcode": str})
for record in df.values:
    (
        Zipcode, ZipCodeType, City, State, LocationType, Lat, Long, Location, 
        Decommisioned, TaxReturnsFiled, EstimatedPopulation, TotalWages,
    ) = record
    primary_zipcode_data[Zipcode] = [
        ZipCodeType, City, State, LocationType, Lat, Long, Location, 
        Decommisioned, TaxReturnsFiled, EstimatedPopulation, TotalWages,
    ]
print("Got %s zipcode primary zipcode." % len(primary_zipcode_data))

# --- read zcta data, construct uszipcode data---
uszipcode_data = list()
df = pd.read_csv("zcta2010.csv", dtype={"ZCTA5": str})
for record in df.values:
    (
        ZCTA5, LANDSQMT, WATERSQMT, LANDSQMI, WATERSQMI, 
        POPULATION, HSGUNITS, INTPTLAT, INTPTLON,
    ) = record
    if (ZCTA5 in geocode_data) and (ZCTA5 in primary_zipcode_data):
        (
            northeastbound_lat, northeastbound_lng, 
            southwestbound_lat, southwestbound_lng, 
            lat_google, lng_google,
        ) = geocode_data[ZCTA5]
          
        (
            ZipCodeType, City, State, LocationType, Lat, Long, Location, 
            Decommisioned, TaxReturnsFiled, EstimatedPopulation, TotalWages,
        ) = primary_zipcode_data[ZCTA5]

        # calculate derived field
        try:
            Density = POPULATION / LANDSQMI
        except:
            Density = None
        try:
            Wealthy = TotalWages / POPULATION
        except:
            Wealthy = None

        if lat_google:
            Lat = lat_google
        if lng_google:
            Long = lng_google

        ZipCodeType = titleize(ZipCodeType)
        City = titleize(City)
        
        uszipcode_data.append([
            Zipcode, ZipCodeType, City, State, POPULATION, Density, 
            TotalWages, Wealthy, HSGUNITS, LANDSQMI, WATERSQMI, 
            Lat, Long, 
            northeastbound_lat, northeastbound_lng, southwestbound_lat, southwestbound_lng,
        ])
print("Got %s zipcode for uszipcode database." % len(uszipcode_data))

uszipcode_data = pd.DataFrame(uszipcode_data, columns=[
    "Zipcode", "ZipcodeType", "City", "State", "Population", "Density", 
    "TotalWages", "Wealthy", "HouseOfUnits", "LandArea", "WaterArea", 
    "Latitude", "Longitude", 
    "NEBoundLatitude", "NEBoundLongitude", "SWBoundLatitude", "SWBoungLongitude", 
])
uszipcode_data.to_csv("zipcode.txt", sep="\t", index=False)