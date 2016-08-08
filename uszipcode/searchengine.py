#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import math
import sqlite3
from heapq import heappush, heappop, nlargest, nsmallest
from functools import total_ordering
from collections import OrderedDict

try:
    from .data import (
        DB_FILE, STATE_ABBR_SHORT_TO_LONG, STATE_ABBR_LONG_TO_SHORT)
    from .packages.haversine import great_circle
    from .packages.fuzzywuzzy.process import extract, extractOne
    from .packages.six import integer_types, string_types
except:
    from uszipcode.data import (
        DB_FILE, STATE_ABBR_SHORT_TO_LONG, STATE_ABBR_LONG_TO_SHORT)
    from uszipcode.packages.haversine import great_circle
    from uszipcode.packages.fuzzywuzzy.process import extract, extractOne
    from uszipcode.packages.six import integer_types, string_types


@total_ordering
class Zipcode(object):

    """Zipcode data container class.

    Attributes:

    - Zipcode: 5 digits string zipcode
    - ZipcodeType: Standard or Po Box
    - City: city full name
    - State: 2 letter short state name
    - Population: estimate population
    - Density:estimate population per square miles (on land only)
    - TotalWages: estimate annual total wage
    - Wealthy: estimate average annual wage = TotalWages/Population
    - HouseOfUnits: estimate number of house unit
    - LandArea: land area in square miles
    - WaterArea: marine area in square miles
    - Latitude: latitude
    - Longitude: longitude
    - NEBoundLatitude: north east bound latitude
    - NEBoundLongitude: north east bound longitude
    - SWBoundLatitude: south west bound latitude
    - SWBoungLongitude: south west bound longitude

    Data typer converter methods:

    - You can use :meth:`~Zipcode.to_json()` method to return json encoded string.
    - You can use :meth:`~Zipcode.to_dict()` method to return dictionary data.
    - You can use :meth:`~Zipcode.to_OrderedDict()` method to return ordered dictionary data.
    - You can use :meth:`~Zipcode.keys()` method to return available attribute list.
    - You can use :meth:`~Zipcode.values()` method to return attributes' values.

    It is hashable, sortable. So ``sort`` and ``set`` method is supported.
    """
    __keys__ = [
        "Zipcode",
        "ZipcodeType",
        "City",
        "State",
        "Population",
        "Density",
        "TotalWages",
        "Wealthy",
        "HouseOfUnits",
        "LandArea",
        "WaterArea",
        "Latitude",
        "Longitude",
        "NEBoundLatitude",
        "NEBoundLongitude",
        "SWBoundLatitude",
        "SWBoungLongitude",
    ]

    def __init__(self,
                 Zipcode=None,  # 5 digits string zipcode
                 ZipcodeType=None,  # Standard or Po Box
                 City=None,  # city full name
                 State=None,  # 2 letter short state name
                 Population=None,  # estimate population
                 # estimate population per square miles (on land only)
                 Density=None,
                 TotalWages=None,  # estimate annual total wage
                 # estimate average annual wage = TotalWages/Population
                 Wealthy=None,
                 HouseOfUnits=None,  # estimate number of house unit
                 LandArea=None,  # land area in square miles
                 WaterArea=None,  # marine area in square miles
                 Latitude=None,  # latitude
                 Longitude=None,  # longitude
                 NEBoundLatitude=None,  # north east bound latitude
                 NEBoundLongitude=None,  # north east bound longitude
                 SWBoundLatitude=None,  # south west bound latitude
                 SWBoungLongitude=None,  # south west bound longitude
                 *args,
                 **kwargs
                 ):
        self.Zipcode = Zipcode
        self.ZipcodeType = ZipcodeType
        self.City = City
        self.State = State
        self.Population = Population
        self.Density = Density
        self.TotalWages = TotalWages
        self.Wealthy = Wealthy
        self.HouseOfUnits = HouseOfUnits
        self.LandArea = LandArea
        self.WaterArea = WaterArea
        self.Latitude = Latitude
        self.Longitude = Longitude
        self.NEBoundLatitude = NEBoundLatitude
        self.NEBoundLongitude = NEBoundLongitude
        self.SWBoundLatitude = SWBoundLatitude
        self.SWBoungLongitude = SWBoungLongitude

    @classmethod
    def _make(cls, keys, values):
        return cls(**dict(zip(keys, values)))

    def __str__(self):
        return json.dumps(self.__dict__, sort_keys=True, indent=4)

    def __repr__(self):
        return json.dumps(self.__dict__, sort_keys=True)

    def __getitem__(self, key):
        return self.__dict__[key]

    def to_dict(self):
        """To Python Dictionary.
        """
        return self.__dict__

    def to_OrderedDict(self):
        """To Python OrderedDict.
        """
        od = OrderedDict()
        for key in Zipcode.__keys__:
            od[key] = self.__dict__.get(key)
        return od

    def __iter__(self):
        return iter(self.values())

    def keys(self):
        """Return Zipcode's available attributes' name in list.
        """
        return list(Zipcode.__keys__)

    def values(self):
        """Return Zipcode's available attributes' value in list.
        """
        values = list()
        for key in Zipcode.__keys__:
            values.append(self.__dict__.get(key))
        return values

    def items(self):
        """Return Zipcode's available attributes' name value pair in list.
        """
        items = list()
        for key in Zipcode.__keys__:
            items.append((key, self.__dict__.get(key)))
        return items

    def to_json(self):
        """To json string.
        """
        return self.__str__()

    def __nonzero__(self):
        """For Python2 bool() method.
        """
        return self.Zipcode is not None

    def __bool__(self):
        """For Python3 bool() method.
        """
        return self.Zipcode is not None

    def __lt__(self, other):
        """For > comparison operator.
        """
        if (self.Zipcode is None) or (other.Zipcode is None):
            raise ValueError(
                "Empty Zipcode instance doesn't support comparison.")
        else:
            return self.Zipcode < other.Zipcode

    def __eq__(self, other):
        """For == comparison operator.
        """
        return self.Zipcode is other.Zipcode

    def __hash__(self):
        """For hash() method
        """
        return hash(self.__dict__["Zipcode"])


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
    DEFAULT_SQL = "SELECT * FROM zipcode"
    DEFAULT_LIMIT = 5

    def __init__(self):
        self.connect = sqlite3.connect(DB_FILE)
        self.connect.row_factory = sqlite3.Row
        self.cursor = self.connect.cursor()

        self.all_column = [record[1] for record in self.cursor.execute(
            "PRAGMA table_info(zipcode)")]
        self.all_column_lowercase = [column.lower()
                                     for column in self.all_column]
        self.all_state_short = [key for key in STATE_ABBR_SHORT_TO_LONG]
        self.all_state_long = [value for value in STATE_ABBR_LONG_TO_SHORT]

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.connect.close()

    def close(self):
        """Closs engine.

        **中文文档**

        断开与数据库的连接。
        """
        self.connect.close()

    def _find_column(self, name):
        """Find matching column name. If failed, return None.

        **中文文档**

        找到与之匹配的正确的column name。
        """
        name = name.lower().strip()
        for column, column_lower in zip(self.all_column, self.all_column_lowercase):
            if name == column_lower:
                return column
        return None

    #--- SQL Helper ---
    def _sql_create_order_by(self, sort_by, ascending):
        """Construct an 'ORDER BY' sql clause.

        :param sort_by: str or list of str, the column you want to sort
        :param descending, bool or list of bool

        **中文文档**

        创建sql中的ORDER BY的部分。
        """
        if sort_by is None:
            return ""

        chunks = list()
        if isinstance(sort_by, string_types) and isinstance(ascending, bool):
            column = self._find_column(sort_by)
            if column is not None:
                if ascending:
                    chunks.append("%s ASC" % column)
                else:
                    chunks.append("%s DESC" % column)
        elif isinstance(sort_by, (tuple, list)) and isinstance(ascending, (tuple, list)) and (len(sort_by) == len(ascending)):
            for column, order in zip(sort_by, ascending):
                column = self._find_column(column)
                if column is not None:
                    if order:
                        chunks.append("%s ASC" % column)
                    else:
                        chunks.append("%s DESC" % column)
        else:
            raise ValueError("invalid 'sort_by', 'descending' input.")

        if len(chunks):
            return "\n\tORDER BY %s" % ", ".join(chunks)
        else:
            return ""

    def _sql_create_limit(self, returns):
        """Construct an 'LIMIT' sql clause.

        :param returns: int

        **中文文档**

        创建sql中的LIMIT的部分。
        """
        if not isinstance(returns, integer_types):
            raise TypeError("'returns' argument has to be an integer.")

        if returns >= 1:
            return "\n\tLIMIT %s" % returns
        else:
            return ""

    def _sql_create_lower_upper(self, column, lower, upper):
        """Return >= and <= sql part.

        **中文文档**

        返回SQL中用于比较值的部分。
        """
        if (lower is None) and (upper is None):
            raise ValueError("'lower' and 'upper' cannot both be None!")

        sql_chunks = list()

        if isinstance(lower, (integer_types, float)):
            sql_chunks.append("%s >= %s" % (column, lower))
        elif lower is None:
            pass
        else:
            raise ValueError("'lower' and 'upper' has to be number or None!")

        if (upper is not None) and isinstance(upper, (integer_types, float)):
            sql_chunks.append("%s <= %s" % (column, upper))
        elif upper is None:
            pass
        else:
            raise ValueError("'lower' and 'upper' has to be number or None!")

        return " AND ".join(sql_chunks)

    def _sql_modify_order_by(self, sql, sort_by, ascending):
        return sql + self._sql_create_order_by(sort_by, ascending)

    def _sql_modify_limit(self, sql, returns):
        return sql + self._sql_create_limit(returns)

    def _sql_modify_standard_only(self, sql, standard_only):
        if standard_only:
            if "WHERE" in sql:
                return sql.replace("WHERE", "WHERE ZipcodeType = 'Standard' AND")
            else:
                return sql + "\n\tWHERE ZipcodeType = 'Standard'"
        else:
            return sql

    def export_to_csv(self, res, abspath):
        """Write result to csv file.

        **中文文档**

        将查询到的Zipcode结果写入csv文件。
        """
        import csv

        with open(abspath, "w") as csvfile:
            writer = csv.DictWriter(csvfile,
                                    delimiter=',', lineterminator="\n",
                                    fieldnames=Zipcode.__keys__,
                                    )
            writer.writeheader()
            for z in res:
                writer.writerow(z.to_dict())

    #--- Search MetaData ---
    def _find_state(self, state, best_match=True):
        """Fuzzy search correct state.

        :param best_match: bool, when True, only one state will return. 
          otherwise, will return all matching states.
        """
        result = list()

        # check if it is a abbreviate name
        if state.upper() in self.all_state_short:
            result.append(state.upper())
        # if not, find out what is the state that user looking for
        else:
            if best_match:
                choice, confidence = extractOne(
                    state.lower(), self.all_state_long)
                if confidence >= 70:
                    result.append(STATE_ABBR_LONG_TO_SHORT[choice])
            else:
                for choice, confidence in extract(state.lower(), self.all_state_long):
                    if confidence >= 70:
                        result.append(STATE_ABBR_LONG_TO_SHORT[choice])

        if len(result) == 0:
            message = ("'%s' is not a valid state name, use 2 letter "
                       "short name or correct full name please.")
            raise ValueError(message % state)

        return result

    def _find_city(self, city, state=None, best_match=True):
        """Fuzzy search correct city.

        :param city: city name.
        :param state: search city in specified state.
        :param best_match: bool, when True, only one city will return. 
          otherwise, will return all matching cities.

        **中文文档**

        如果给定了state, 则只在state里的城市中寻找, 否则, 在全国所有的城市中
        寻找。 
        """
        # find out what is the city that user looking for
        if state:
            state = self._find_state(state, best_match=True)[0]
            select_sql = "SELECT DISTINCT City FROM zipcode WHERE State == '%s'" % state
        else:
            select_sql = "SELECT DISTINCT City FROM zipcode"

        all_city = [row[0] for row in self.cursor.execute(select_sql)]
        if len(all_city) == 0:
            raise ValueError("No city is available in state('%s')" % state)

        result = list()

        if best_match:
            choice, confidence = extractOne(city.lower(), all_city)
            if confidence >= 70:
                result.append(choice)
        else:
            for choice, confidence in extract(city.lower(), all_city):
                if confidence >= 70:
                    result.append(choice)

        if len(result) == 0:
            raise ValueError("'%s' is not a valid city name" % city)

        return result

    #--- Search ---
    def by_zipcode(self, zipcode, standard_only=True):
        """Search zipcode information.

        :param zipcode: integer or string zipcode, no zero pad needed
        :param standard_only: bool, default True, only returns standard 
          type zipcode

        **中文文档**

        查询某一个Zipcode的具体信息。
        """
        # convert zipcode to 5 digits string
        zipcode = ("%s" % zipcode).zfill(5)

        # execute query
        select_sql = "SELECT * FROM zipcode WHERE Zipcode = '%s'" % zipcode
        select_sql = self._sql_modify_standard_only(select_sql, standard_only)

        res = self.cursor.execute(select_sql).fetchall()
        if len(res) == 1:
            return Zipcode(**res[0])
        elif len(res) == 0:
            return Zipcode()
        else:
            raise Exception("by_zipcode can not return multiple zipcode!")

    def by_coordinate(self, lat, lng, radius=50.0, ascending=True, standard_only=True,
                      returns=DEFAULT_LIMIT):
        """Search zipcode information near a coordinate on a map. May return
        multiple results.

        :param lat: center latitude
        :param lng: center lngitude
        :param radius: for the inside implementation only, search zipcode 
          within #radius units of lat, lng
        :param ascending: bool, if True, sort by distance from closest
        :param standard_only: bool, default True, only returns standard 
          type zipcode
        :param returns: returns at most how many results

        **中文文档**

        1. 计算出在中心坐标处, 每一经度和纬度分别代表多少miles。
        2. 以给定坐标为中心, 画出一个矩形, 长宽分别为半径的1.2倍左右, 找到该
          矩形内所有的Zipcode。
        3. 对这些Zipcode计算出他们的距离, 然后按照距离远近排序。距离超过我们
          限定的半径的直接丢弃。
        """
        return self.find(lat=lat, lng=lng, radius=radius, standard_only=standard_only, sort_by=None, ascending=ascending, returns=returns)

    def by_city_and_state(self, city, state,
                          standard_only=True,
                          sort_by="ZipCode", ascending=True,
                          returns=DEFAULT_LIMIT,
                          ):
        """Search zipcode information by City and State name.

        You can use either short state name and long state name. My engine use
        fuzzy match and guess what is you want.

        :param city: city name.
        :param state: 2 letter short name or long name.
        :param standard_only: bool, default True, only returns standard 
          type zipcode
        :param sort_by: str or list of str, default ``"Zipcode"``
        :param ascending: bool or list of bool, default True
        :param returns: int, default 5

        **中文文档**

        根据城市和州, 模糊查询。
        """
        return self.find(city=city,
                         state=state,
                         standard_only=standard_only,
                         sort_by=sort_by,
                         ascending=ascending,
                         returns=returns)

    def by_city(self, city,
                standard_only=True,
                sort_by="ZipCode", ascending=True,
                returns=DEFAULT_LIMIT,
                ):
        """Search zipcode information by City name.

        My engine use fuzzy match and guess what is the city you want.

        :param city: city name.
        :param standard_only: bool, default True, only returns standard 
          type zipcode
        :param sort_by: str or list of str, default ``"Zipcode"``
        :param ascending: bool or list of bool, default True
        :param returns: int, default 5

        **中文文档**

        根据城市, 模糊查询。
        """
        return self.find(city=city,
                         standard_only=standard_only,
                         sort_by=sort_by,
                         ascending=ascending,
                         returns=returns)

    def by_state(self, state,
                 standard_only=True,
                 sort_by="ZipCode", ascending=True,
                 returns=DEFAULT_LIMIT,
                 ):
        """Search zipcode information by State name.

        You can use either short state name and long state name. My engine use
        fuzzy match and guess what is the state you want.

        :param state: 2 letter short name or long name.
        :param standard_only: bool, default True, only returns standard 
          type zipcode
        :param sort_by: str or list of str, default ``"Zipcode"``
        :param ascending: bool or list of bool, default True
        :param returns: int, default 5

        **中文文档**

        根据州, 模糊查询。
        """
        return self.find(state=state,
                         standard_only=standard_only,
                         sort_by=sort_by,
                         ascending=ascending,
                         returns=returns)

    def by_prefix(self, prefix,
                  standard_only=True,
                  sort_by="ZipCode", ascending=True,
                  returns=DEFAULT_LIMIT,
                  ):
        """Search zipcode information by first N numbers.

        :param prefix: first N zipcode number
        :param standard_only: bool, default True, only returns standard 
          type zipcode
        :param sort_by: str or list of str, default ``"Zipcode"``
        :param ascending: bool or list of bool, default True
        :param returns: int, default 5

        **中文文档**

        根据Zipcode的前面几个字符模糊查询。
        """
        # exam input
        return self.find(prefix=prefix,
                         standard_only=standard_only,
                         sort_by=sort_by,
                         ascending=ascending,
                         returns=returns)

    def by_pattern(self, pattern,
                   standard_only=True,
                   sort_by="ZipCode", ascending=True,
                   returns=DEFAULT_LIMIT,
                   ):
        """Search zipcode by wildcard.

        :param prefix: first N zipcode number
        :param standard_only: bool, default True, only returns standard 
          type zipcode
        :param sort_by: str or list of str, default ``"Zipcode"``
        :param ascending: bool or list of bool, default True
        :param returns: int, default 5

        **中文文档**

        根据Zipcode的中间的字符模糊查询。
        """
        return self.find(pattern=pattern,
                         standard_only=standard_only,
                         sort_by=sort_by,
                         ascending=ascending,
                         returns=returns)

    def by_population(self, lower=-1, upper=2**30,
                      standard_only=True,
                      sort_by="ZipCode", ascending=True,
                      returns=DEFAULT_LIMIT,
                      ):
        """Search zipcode information by population range.

        :param lower: minimal population
        :param upper: maximum population
        :param standard_only: bool, default True, only returns standard 
          type zipcode
        :param sort_by: str or list of str, default ``"Zipcode"``
        :param ascending: bool or list of bool, default True
        :param returns: int, default 5

        **中文文档**

        根据人口的上下限查询。
        """
        return self.find(population_lower=lower,
                         population_upper=upper,
                         standard_only=standard_only,
                         sort_by=sort_by,
                         ascending=ascending,
                         returns=returns)

    def by_density(self, lower=-1, upper=2**30,
                   standard_only=True,
                   sort_by="ZipCode", ascending=True,
                   returns=DEFAULT_LIMIT,
                   ):
        """Search zipcode information by population density range.

        population density = population per square miles

        :param lower: minimal population
        :param upper: maximum population
        :param standard_only: bool, default True, only returns standard 
          type zipcode
        :param sort_by: str or list of str, default ``"Zipcode"``
        :param ascending: bool or list of bool, default True
        :param returns: int, default 5

        **中文文档**

        根据每平方Mile的人口密度模糊查询。
        """
        return self.find(density_lower=lower,
                         density_upper=upper,
                         standard_only=standard_only,
                         sort_by=sort_by,
                         ascending=ascending,
                         returns=returns)

    def by_landarea(self, lower=-1, upper=2**30,
                    standard_only=True,
                    sort_by="ZipCode", ascending=True,
                    returns=DEFAULT_LIMIT,
                    ):
        """Search zipcode information by landarea range.

        :param lower: minimal landarea in sqrt miles
        :param upper: maximum landarea in sqrt miles
        :param standard_only: bool, default True, only returns standard 
          type zipcode
        :param sort_by: str or list of str, default ``"Zipcode"``
        :param ascending: bool or list of bool, default True
        :param returns: int, default 5

        **中文文档**

        根据陆地面积模糊查询。
        """
        return self.find(landarea_lower=lower,
                         landarea_upper=upper,
                         standard_only=standard_only,
                         sort_by=sort_by,
                         ascending=ascending,
                         returns=returns)

    def by_waterarea(self, lower=-1, upper=2**30,
                     standard_only=True,
                     sort_by="ZipCode", ascending=True,
                     returns=DEFAULT_LIMIT,
                     ):
        """Search zipcode information by waterarea range.

        :param lower: minimal waterarea in sqrt miles
        :param upper: maximum waterarea in sqrt miles
        :param standard_only: bool, default True, only returns standard 
          type zipcode
        :param sort_by: str or list of str, default ``"Zipcode"``
        :param ascending: bool or list of bool, default True
        :param returns: int, default 5

        **中文文档**

        根据水域面积模糊查询。
        """
        return self.find(waterarea_lower=lower,
                         waterarea_upper=upper,
                         standard_only=standard_only,
                         sort_by=sort_by,
                         ascending=ascending,
                         returns=returns)

    def by_totalwages(self, lower=-1, upper=2**30,
                      standard_only=True,
                      sort_by="ZipCode", ascending=True,
                      returns=DEFAULT_LIMIT,
                      ):
        """Search zipcode information by total annual wages.

        :param lower: minimal total annual wages
        :param upper: maximum total annual wages
        :param standard_only: bool, default True, only returns standard 
          type zipcode
        :param sort_by: str or list of str, default ``"Zipcode"``
        :param ascending: bool or list of bool, default True
        :param returns: int, default 5

        **中文文档**

        根据总年度工资收入模糊查询。
        """
        return self.find(totalwages_lower=lower,
                         totalwages_upper=upper,
                         standard_only=standard_only,
                         sort_by=sort_by,
                         ascending=ascending,
                         returns=returns)

    def by_wealthy(self, lower=-1, upper=2**30,
                   standard_only=True,
                   sort_by="ZipCode", ascending=True,
                   returns=DEFAULT_LIMIT,
                   ):
        """Search zipcode information by average annual wage (AAW).

        AAW = total wage / population

        :param lower: minimal AAW
        :param upper: maximum AAW
        :param standard_only: bool, default True, only returns standard 
          type zipcode
        :param sort_by: str or list of str, default ``"Zipcode"``
        :param ascending: bool or list of bool, default True
        :param returns: int, default 5

        **中文文档**

        根据人均年收入模糊查询。
        """
        return self.find(wealthy_lower=lower,
                         wealthy_upper=upper,
                         standard_only=standard_only,
                         sort_by=sort_by,
                         ascending=ascending,
                         returns=returns)

    def by_house(self, lower=-1, upper=2**30,
                 standard_only=True,
                 sort_by="ZipCode", ascending=True,
                 returns=DEFAULT_LIMIT,
                 ):
        """Search zipcode information by house of units.

        :param lower: minimal house of units
        :param upper: maximum house of units
        :param standard_only: bool, default True, only returns standard 
          type zipcode
        :param sort_by: str or list of str, default ``"Zipcode"``
        :param ascending: bool or list of bool, default True
        :param returns: int, default 5

        **中文文档**

        根据房屋数量, 包括Townhouse, Single House模糊查询。
        """
        return self.find(house_lower=lower,
                         house_upper=upper,
                         standard_only=standard_only,
                         sort_by=sort_by,
                         ascending=ascending,
                         returns=returns)

    def find(self,
             lat=None, lng=None, radius=None,
             city=None, state=None,
             prefix=None,
             pattern=None,
             population_lower=None, population_upper=None,
             density_lower=None, density_upper=None,
             landarea_lower=None, landarea_upper=None,
             waterarea_lower=None, waterarea_upper=None,
             totalwages_lower=None, totalwages_upper=None,
             wealthy_lower=None, wealthy_upper=None,
             house_lower=None, house_upper=None,
             standard_only=True,
             sort_by="ZipCode", ascending=True,
             returns=DEFAULT_LIMIT,
             ):
        """
        :params sort_by: can be attribute name or 'Dist'.
        """
        where_chunks = list()

        #--- by_coordinate ---
        if isinstance(lat, (integer_types, float)) and \
                isinstance(lat, (integer_types, float)) and \
                isinstance(radius, (integer_types, float)):
            flag_by_coordinate = True
            if radius <= 0:
                return []

            # define lat lng boundary
            dist_btwn_lat_deg = 69.172
            dist_btwn_lon_deg = math.cos(lat) * 69.172
            lat_degr_rad = abs(radius * 1.0 / dist_btwn_lat_deg)
            lon_degr_rad = abs(radius * 1.0 / dist_btwn_lon_deg)

            lat_lower = lat - lat_degr_rad
            lat_upper = lat + lat_degr_rad
            lng_lower = lng - lon_degr_rad
            lng_upper = lng + lon_degr_rad

            where_chunks.append("Latitude >= %s" % lat_lower)
            where_chunks.append("Latitude <= %s" % lat_upper)
            where_chunks.append("Longitude >= %s" % lng_lower)
            where_chunks.append("Longitude <= %s" % lng_upper)

            if (sort_by is None) or (sort_by == "Dist"):
                flag_sort_by = False
            else:
                flag_sort_by = True
        else:
            flag_by_coordinate = False

        #--- by city or state ---
        if (state is not None) and (city is not None):
            state = self._find_state(state, best_match=True)[0]
            city = self._find_city(city, state, best_match=True)[0]
            where_chunks.append("State = '%s' AND City = '%s'" % (state, city))
        elif (state is not None) and (city is None):
            state = self._find_state(state, best_match=True)[0]
            where_chunks.append("State = '%s'" % state)
        elif (state is None) and (city is not None):
            city = self._find_city(city, None, best_match=True)[0]
            where_chunks.append("City = '%s'" % city)
        else:
            pass

        #--- by prefix ---
        if prefix is not None:
            if not isinstance(prefix, string_types):
                raise TypeError("prefix has to be a string")
            if (not prefix.isdigit()) and (1 <= len(prefix) <= 5):
                raise ValueError("prefix has to be a 1-5 letter digits")
            where_chunks.append("Zipcode LIKE '%s%%'" % prefix)

        #--- by pattern ---
        if pattern is not None:
            if not isinstance(pattern, string_types):
                raise TypeError("pattern has to be a string")
            if (not pattern.isdigit()) and (1 <= len(pattern) <= 5):
                raise ValueError("pattern has to be a 1-5 letter digits")
            where_chunks.append("Zipcode LIKE '%%%s%%' " % pattern)

        #--- by population ---
        try:
            sql = self._sql_create_lower_upper(
                "Population", population_lower, population_upper)
            where_chunks.append(sql)
        except ValueError:
            pass

        #--- by density ---
        try:
            sql = self._sql_create_lower_upper(
                "Density", density_lower, density_upper)
            where_chunks.append(sql)
        except ValueError:
            pass

        #--- by land area ---
        try:
            sql = self._sql_create_lower_upper(
                "LandArea", landarea_lower, landarea_upper)
            where_chunks.append(sql)
        except ValueError:
            pass

        #--- by water area ---
        try:
            sql = self._sql_create_lower_upper(
                "WaterArea", waterarea_lower, waterarea_upper)
            where_chunks.append(sql)
        except ValueError:
            pass

        #--- by total wages ---
        try:
            sql = self._sql_create_lower_upper(
                "TotalWages", totalwages_lower, totalwages_upper)
            where_chunks.append(sql)
        except ValueError:
            pass

        #--- by wealthy ---
        try:
            sql = self._sql_create_lower_upper(
                "Wealthy", wealthy_lower, wealthy_upper)
            where_chunks.append(sql)
        except ValueError:
            pass

        #--- by house ---
        try:
            sql = self._sql_create_lower_upper(
                "HouseOfUnits", house_lower, house_upper)
            where_chunks.append(sql)
        except ValueError:
            pass

        select_sql = "SELECT * FROM zipcode \n\tWHERE %s" % " AND ".join(
            where_chunks)
        select_sql = self._sql_modify_standard_only(select_sql, standard_only)
        select_sql = self._sql_modify_order_by(select_sql, sort_by, ascending)

        #--- solve coordinate and other search sort_by conflict ---
        if flag_by_coordinate:
            # has sort_by keyword, order by keyword
            # 有sort_by关键字的情况下, 按关键字排序
            if flag_sort_by:
                res = list()
                for row in self.cursor.execute(select_sql):
                    dist = great_circle(
                        (row["Latitude"], row["Longitude"]), (lat, lng))
                    if dist <= radius:
                        res.append(Zipcode(**row))
                        if len(res) == returns:
                            return res
            # no sort by keyword, then sort from cloest to farturest
            # 没有sort_by关键字, 按距离远近排序
            else:
                # use heap sort find top N closest zipcode
                def gen():
                    for row in self.cursor.execute(select_sql):
                        dist = great_circle(
                            (row["Latitude"], row["Longitude"]), (lat, lng))
                        if dist <= radius:
                            yield (dist, row)

                if returns >= 1:

                    if ascending:
                        data = nsmallest(returns, gen(), key=lambda x: x[0])
                    else:
                        data = nlargest(returns, gen(), key=lambda x: x[0])
                else:
                    if ascending:
                        data = sorted(
                            gen(), key=lambda x: x[0], reverse=not ascending)

                res = [Zipcode(**row) for dist, row in data]
        else:
            select_sql = self._sql_modify_limit(select_sql, returns)
            res = [Zipcode(**row) for row in self.cursor.execute(select_sql)]

        return res

    def all(self):
        """Return all available zipcode data in this database.

        Warning! This may takes long.

        **中文文档**

        返回所有Zipcode。
        """
        select_sql = "SELECT * FROM zipcode"
        res = [Zipcode(**row) for row in self.cursor.execute(select_sql)]
        return res
