#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uszipcode.data import (
    DB_FILE, STATE_ABBR_SHORT_TO_LONG, STATE_ABBR_LONG_TO_SHORT)
from uszipcode.packages.haversine import great_circle
from uszipcode.packages.fuzzywuzzy.process import extractOne
from collections import OrderedDict
from heapq import *
import sqlite3
import math
import json

class Zipcode(object):
    """Zipcode class. Attributes includes:
    
    - Zipcode: 5 digits string zipcode
    - ZipcodeType: Standard or Po Box
    - City: city full name
    - State: 2 letter short state name
    - Population: estimate population
    - Density: estimate population per square miles (on land only)
    - TotalWages: estimate annual total wage
    - Wealthy: estimate average annual wage
    - HouseOfUnits: estimate number of house unit
    - LandArea: land area in square miles
    - WaterArea: marine area in square miles
    - Latitude: latitude
    - Longitude: longitude
    - NEBoundLatitude: north east bound latitude
    - NEBoundLongitude: north east bound longitude
    - SWBoundLatitude: south west bound latitude
    - SWBoungLongitude: south west bound longitude
    
    There are two method you may need:
    
    - You can use :meth:`~Zipcode.to_json` method to return json encoded string.
    - You can use :meth:`~Zipcode.to_dict` method to return dictionary data.
    """
    def __init__(self, keys, values):
        for k, v in zip(keys, values):
            object.__setattr__(self, k, v)
        try:
            self.Density = self.Population/self.LandArea
        except:
            self.Density = None
        try:
            self.Wealthy = self.TotalWages/self.Population
        except:
            self.Wealthy = None
            
    def __str__(self):
        return json.dumps(self.__dict__, 
            sort_keys=True, indent=4, separators=("," , ": "))
    
    def __repr__(self):
        return json.dumps(self.__dict__, sort_keys=True)
    
    def __getitem__(self, key):
        return self.__dict__[key]
    
    def to_dict(self):
        return self.__dict__
    
    def to_json(self):
        return self.__str__()

_DEFAULT_LIMIT = 5

class ZipcodeSearchEngine(object):
    """A fast, powerful index optimized zipcode object search engine class.
    
    Quick links:
    
    - :meth:`ZipcodeSearchEngine.by_zipcode`
    - :meth:`ZipcodeSearchEngine.by_coordinate`
    - :meth:`ZipcodeSearchEngine.by_city_and_state`
    - :meth:`ZipcodeSearchEngine.by_city`
    - :meth:`ZipcodeSearchEngine.by_state`
    - :meth:`ZipcodeSearchEngine.by_prefix`
    - :meth:`ZipcodeSearchEngine.by_pattern`
    - :meth:`ZipcodeSearchEngine.by_population`
    - :meth:`ZipcodeSearchEngine.by_density`
    - :meth:`ZipcodeSearchEngine.by_landarea`
    - :meth:`ZipcodeSearchEngine.by_waterarea`
    - :meth:`ZipcodeSearchEngine.by_totalwages`
    - :meth:`ZipcodeSearchEngine.by_wealthy`
    - :meth:`ZipcodeSearchEngine.by_house`
    """
    _standard_only_param = "AND ZipcodeType = 'Standard'"
    def __init__(self):
        self.connect = sqlite3.connect(DB_FILE)
        self.connect.row_factory = sqlite3.Row
        self.cursor = self.connect.cursor()
        
        self.all_column = [record[1] for record in self.cursor.execute(
            "PRAGMA table_info(zipcode)")]
        self.all_state_short = [key for key in STATE_ABBR_SHORT_TO_LONG]
        self.all_state_long = [value for value in STATE_ABBR_LONG_TO_SHORT]
        
    def __enter__(self):
        return self
    
    def __exit__(self, *exc_info):
        self.connect.close()
        
    def close(self):
        """Closs engine.
        """
        self.connect.close()

    def get_sortby_sql(self, sortby, descending):
        """Construct an ORDER BY SQL.
        """
        if sortby in self.all_column: 
            if descending:
                sortby_sql = " ORDER BY %s DESC" % sortby
            else:
                sortby_sql = " ORDER BY %s ASC" % sortby
        else:
            sortby_sql = ""
        return sortby_sql

    def get_limit_sql(self, returns):
        """Construct an LIMIT XXX SQL.
        """
        if not isinstance(returns, int):
            raise TypeError("returns argument has to be an integer.")
        
        if returns >= 1:
            limit_sql = "LIMIT %s" % returns
        else:
            limit_sql = ""
        
        return limit_sql

    def by_zipcode(self, zipcode, standard_only=True):
        """Search zipcode information.
        
        :param zipcode: integer or string zipcode, no zero pad needed
        :param standard_only: boolean, default True, only returns standard 
          type zipcode
        """
        # convert zipcode to 5 digits string
        zipcode = ("%s" % zipcode).zfill(5)
        
        # execute query
        select_sql = "SELECT * FROM zipcode WHERE Zipcode = '%s'" % zipcode
        if standard_only:
            select_sql = select_sql + self._standard_only_param
        
        for row in self.cursor.execute(select_sql):
            return Zipcode(self.all_column, list(row))
        
        return None
    
    def by_coordinate(self, lat, lng, radius=20, standard_only=True, 
                      returns=_DEFAULT_LIMIT):
        """Search zipcode information near a coordinate on a map. May return
        multiple results.
        
        :param lat: center latitude
        :param lng: center lngitude
        :param radius: for the inside implementation only, search zipcode 
          within #radius units of lat, lng
        :param standard_only: boolean, default True, only returns standard 
          type zipcode
        :param returns: returns at most how many results
        """
        # define lat lng boundary
        dist_btwn_lat_deg = 69.172
        dist_btwn_lon_deg = math.cos(lat) * 69.172
        lat_degr_rad = radius * 1.0/dist_btwn_lat_deg
        lon_degr_rad = radius * 1.0/dist_btwn_lon_deg
    
        lat_lower = lat - lat_degr_rad
        lat_upper = lat + lat_degr_rad
        lng_lower = lng - lon_degr_rad
        lng_upper = lng + lon_degr_rad
        
        # execute query
        select_sql = \
        """
        SELECT * FROM zipcode 
        WHERE
            Latitude >= %s 
            AND Latitude <= %s
            AND Longitude >= %s
            AND Longitude <= %s
        """ % (lat_lower, lat_upper, lng_lower, lng_upper)
        if standard_only:
            select_sql = select_sql + self._standard_only_param

        # use heap sort find 5 closest zipcode
        heap = list()
        for row in self.cursor.execute(select_sql):
            dist = great_circle((row["Latitude"], row["Longitude"]), (lat, lng))
            heappush(heap, [dist,] + list(row))
            
        # generate results
        res = list()
        if returns >= 1:
            for i in range(returns):
                try:
                    res.append(
                        Zipcode(self.all_column, heappop(heap)[1:])
                    )
                except:
                    pass
        elif returns == 0:
            while heap:
                res.append(
                    Zipcode(self.all_column, heappop(heap)[1:])
                )
        return res
    
    def by_city_and_state(self, city, state, standard_only=True):
        """Search zipcode information by City and State name.
        
        You can use either short state name and long state name. My engine use
        fuzzy match and guess what is you want.
        
        :param city: city name.
        :param state: 2 letter short name or long name.
        :param standard_only: boolean, default True, only returns standard 
          type zipcode
        """
        # check if it is a abbreviate name
        if state.upper() in self.all_state_short:
            state = state.upper()
        # if not, find out what is the state that user looking for
        else:
            choice, confidence = extractOne(state.lower(), self.all_state_long)
            if confidence < 70:
                raise Exception("'%s' is not a valid statename, use 2 letter "
                                "short name or correct full name please." % state)
            state = STATE_ABBR_LONG_TO_SHORT[choice]
        
        # find out what is the city that user looking for
        select_sql = "SELECT City FROM zipcode WHERE State == '%s'" % state
        all_city = [record[0] for record in self.cursor.execute(select_sql)]
        
        choice, confidence = extractOne(city.lower(), all_city)
        if confidence < 70:
            raise Exception("Cannot found '%s' in '%s'." % (city, state))
        else:
            city = choice
        
        # execute query
        select_sql = \
        """
        SELECT * FROM zipcode 
        WHERE 
            City = '%s' 
            AND State = '%s'
        """ % (city, state)
        if standard_only:
            select_sql = select_sql + self._standard_only_param

        res = list()
        for row in self.cursor.execute(select_sql):
            res.append(Zipcode(self.all_column, list(row)))
        
        return res

    def by_city(self, city, standard_only=True):
        """Search zipcode information by City and State name.
        
        My engine use fuzzy match and guess what is you want.
        
        :param city: city name.
        :param standard_only: boolean, default True, only returns standard 
          type zipcode
        """
        # find out what is the city that user looking for
        select_sql = "SELECT City FROM zipcode WHERE City == '%s'" % city
        all_city = [record[0] for record in self.cursor.execute(select_sql)]
        
        choice, confidence = extractOne(city.lower(), all_city)
        if confidence < 70:
            raise Exception("Cannot found '%s' in '%s'." % (city, state))
        else:
            city = choice

        # execute query
        select_sql = \
        """
        SELECT * FROM zipcode 
        WHERE City = '%s'
        """ % (city,)
        if standard_only:
            select_sql = select_sql + self._standard_only_param

        res = list()
        for row in self.cursor.execute(select_sql):
            res.append(Zipcode(self.all_column, list(row)))
        
        return res
    
    def by_state(self, state, standard_only=True):
        """Search zipcode information by State name.
        
        You can use either short state name and long state name. My engine use
        fuzzy match and guess what is you want.
        
        :param state: 2 letter short name or long name.
        :param standard_only: boolean, default True, only returns standard 
          type zipcode
        """
        # check if it is a abbreviate name
        if state.upper() in self.all_state_short:
            state = state.upper()
        # if not, find out what is the state that user looking for
        else:
            choice, confidence = extractOne(state.lower(), self.all_state_long)
            if confidence < 70:
                raise Exception("'%s' is not a valid statename, use 2 letter "
                                "short name or correct full name please." % state)
            state = STATE_ABBR_LONG_TO_SHORT[choice]

        # execute query
        select_sql = \
        """
        SELECT * FROM zipcode 
        WHERE State = '%s'
        """ % (state,)
        if standard_only:
            select_sql = select_sql + self._standard_only_param

        res = list()
        for row in self.cursor.execute(select_sql):
            res.append(Zipcode(self.all_column, list(row)))
        
        return res
    
    def by_prefix(self, prefix, standard_only=True, 
            sortby="ZipCode", descending=False, returns=_DEFAULT_LIMIT):
        """Search zipcode information by first N numbers.
        
        :param prefix: first N zipcode number
        :param standard_only: boolean, default True, only returns standard 
          type zipcode
        :param sortby: string, default ``"Zipcode"``
        :param descending: boolean, default False
        :param returns: int, default 5
        """
        # exam input
        if not isinstance(prefix, str):
            raise TypeError("prefix has to be a string")
        if not prefix.isdigit():
            raise ValueError("prefix has to be a 1-5 letter digits")
        
        # execute query
        select_sql = "SELECT * FROM zipcode WHERE Zipcode LIKE '%s%%' " % prefix
        if standard_only:
            select_sql = select_sql + self._standard_only_param
        select_sql = select_sql + self.get_sortby_sql(sortby, descending)
        select_sql = select_sql + self.get_limit_sql(returns)
        
        res = list()
        for row in self.cursor.execute(select_sql):
            res.append(Zipcode(self.all_column, list(row)))
        
        return res

    def by_pattern(self, pattern, standard_only=True, 
            sortby="ZipCode", descending=False, returns=_DEFAULT_LIMIT):
        """Search zipcode information by first N numbers.
        
        :param prefix: first N zipcode number
        :param standard_only: boolean, default True, only returns standard 
          type zipcode
        :param sortby: string, default ``"Zipcode"``
        :param descending: boolean, default False
        :param returns: int, default 5
        """
        # exam input
        if not isinstance(pattern, str):
            raise TypeError("prefix has to be a string")
        if not pattern.isdigit():
            raise ValueError("prefix has to be a 1-5 letter digits")
        
        # execute query
        select_sql = "SELECT * FROM zipcode WHERE Zipcode LIKE '%%%s%%' " % pattern
        if standard_only:
            select_sql = select_sql + self._standard_only_param
        select_sql = select_sql + self.get_sortby_sql(sortby, descending)
        select_sql = select_sql + self.get_limit_sql(returns)
        
        res = list()
        for row in self.cursor.execute(select_sql):
            res.append(Zipcode(self.all_column, list(row)))
        
        return res

    def by_population(self, lower=-1, upper=2**30, standard_only=True, 
            sortby="ZipCode", descending=False, returns=_DEFAULT_LIMIT):
        """Search zipcode information by population range.
        
        :param lower: minimal population
        :param upper: maximum population
        :param standard_only: boolean, default True, only returns standard 
          type zipcode
        :param sortby: string, default ``"Zipcode"``
        :param descending: boolean, default False
        :param returns: int, default 5
        """
        select_sql = \
        """
        SELECT * FROM zipcode WHERE 
            Population >= %f AND Population <= %f
        """ % (lower, upper)
        if standard_only:
            select_sql = select_sql + self._standard_only_param
        select_sql = select_sql + self.get_sortby_sql(sortby, descending)
        select_sql = select_sql + self.get_limit_sql(returns)
        
        res = list()
        for row in self.cursor.execute(select_sql):
            res.append(Zipcode(self.all_column, list(row)))
        return res
    
    def by_density(self, lower=-1, upper=2**30, standard_only=True, 
            sortby="ZipCode", descending=False, returns=_DEFAULT_LIMIT):
        """Search zipcode information by population density range.
        
        population density = population / per square miles
        
        :param lower: minimal population
        :param upper: maximum population
        :param standard_only: boolean, default True, only returns standard 
          type zipcode
        :param sortby: string, default ``"Zipcode"``
        :param descending: boolean, default False
        :param returns: int, default 5
        """
        select_sql = \
        """
        SELECT * FROM zipcode WHERE Density >= %f AND Density <= %f
        """ % (lower, upper)
        if standard_only:
            select_sql = select_sql + self._standard_only_param
        select_sql = select_sql + self.get_sortby_sql(sortby, descending)
        select_sql = select_sql + self.get_limit_sql(returns)
        
        res = list()
        for row in self.cursor.execute(select_sql):
            res.append(Zipcode(self.all_column, list(row)))
        return res

    def by_landarea(self, lower=-1, upper=2**30, standard_only=True, 
            sortby="ZipCode", descending=False, returns=_DEFAULT_LIMIT):
        """Search zipcode information by landarea range.
        
        :param lower: minimal landarea
        :param upper: maximum landarea
        :param standard_only: boolean, default True, only returns standard 
          type zipcode
        :param sortby: string, default ``"Zipcode"``
        :param descending: boolean, default False
        :param returns: int, default 5
        """
        select_sql = \
        """
        SELECT * FROM zipcode WHERE LandArea >= %f AND LandArea <= %f
        """ % (lower, upper)
        if standard_only:
            select_sql = select_sql + self._standard_only_param
        select_sql = select_sql + self.get_sortby_sql(sortby, descending)
        select_sql = select_sql + self.get_limit_sql(returns)
        
        res = list()
        for row in self.cursor.execute(select_sql):
            res.append(Zipcode(self.all_column, list(row)))
        return res

    def by_waterarea(self, lower=-1, upper=2**30, standard_only=True, 
            sortby="ZipCode", descending=False, returns=_DEFAULT_LIMIT):
        """Search zipcode information by landarea range.
        
        :param lower: minimal waterarea
        :param upper: maximum waterarea
        :param standard_only: boolean, default True, only returns standard 
          type zipcode
        :param sortby: string, default ``"Zipcode"``
        :param descending: boolean, default False
        :param returns: int, default 5
        """
        select_sql = \
        """
        SELECT * FROM zipcode WHERE WaterArea >= %f AND WaterArea <= %f
        """ % (lower, upper)
        if standard_only:
            select_sql = select_sql + self._standard_only_param
        select_sql = select_sql + self.get_sortby_sql(sortby, descending)
        select_sql = select_sql + self.get_limit_sql(returns)
        
        res = list()
        for row in self.cursor.execute(select_sql):
            res.append(Zipcode(self.all_column, list(row)))
        return res
    
    def by_totalwages(self, lower=-1, upper=2**30, standard_only=True, 
            sortby="ZipCode", descending=False, returns=_DEFAULT_LIMIT):
        """Search zipcode information by total annual wages.
        
        :param lower: minimal total annual wages
        :param upper: maximum total annual wages
        :param standard_only: boolean, default True, only returns standard 
          type zipcode
        :param sortby: string, default ``"Zipcode"``
        :param descending: boolean, default False
        :param returns: int, default 5
        """            
        select_sql = \
        """
        SELECT * FROM zipcode WHERE TotalWages >= %f AND TotalWages <= %f
        """ % (lower, upper)
        if standard_only:
            select_sql = select_sql + self._standard_only_param
        select_sql = select_sql + self.get_sortby_sql(sortby, descending)
        select_sql = select_sql + self.get_limit_sql(returns)
        
        res = list()
        for row in self.cursor.execute(select_sql):
            res.append(Zipcode(self.all_column, list(row)))
        return res
 
    def by_wealthy(self, lower=-1, upper=2**30, standard_only=True, 
            sortby="ZipCode", descending=False, returns=_DEFAULT_LIMIT):
        """Search zipcode information by average annual wage (AAW).
        
        AAW = total wage / population
        
        :param lower: minimal AAW
        :param upper: maximum AAW
        :param sortby: string, default ``"Zipcode"``
        :param descending: boolean, default False
        :param returns: int, default 5
        """            
        select_sql = \
        """
        SELECT * FROM zipcode WHERE 
            TotalWages / Population >= %f AND TotalWages / Population <= %f
        """ % (lower, upper)
        if standard_only:
            select_sql = select_sql + self._standard_only_param
        select_sql = select_sql + self.get_sortby_sql(sortby, descending)
        select_sql = select_sql + self.get_limit_sql(returns)
        
        res = list()
        for row in self.cursor.execute(select_sql):
            res.append(Zipcode(self.all_column, list(row)))
        return res
    
    def by_house(self, lower=-1, upper=2**30, standard_only=True, 
            sortby="ZipCode", descending=False, returns=_DEFAULT_LIMIT):
        """Search zipcode information by house of units.
        
        :param lower: minimal house of units
        :param upper: maximum house of units
        :param sortby: string, default ``"Zipcode"``
        :param descending: boolean, default False
        :param returns: int, default 5
        """            
        select_sql = \
        """
        SELECT * FROM zipcode WHERE 
            HouseOfUnits >= %f AND HouseOfUnits <= %f
        """ % (lower, upper)
        if standard_only:
            select_sql = select_sql + self._standard_only_param
        select_sql = select_sql + self.get_sortby_sql(sortby, descending)
        select_sql = select_sql + self.get_limit_sql(returns)
        
        res = list()
        for row in self.cursor.execute(select_sql):
            res.append(Zipcode(self.all_column, list(row)))
        return res