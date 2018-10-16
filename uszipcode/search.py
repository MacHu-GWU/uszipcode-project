#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module allows developer to query zipcode with super clean API.
"""

import sys
import math
import heapq

from collections import OrderedDict
from sqlalchemy.orm import sessionmaker
from six import integer_types, string_types

from .db import (
    is_simple_db_file_exists, is_db_file_exists,
    connect_to_simple_zipcode_db, connect_to_zipcode_db,
    download_simple_db_file, download_db_file
)
from .model import SimpleZipcode, Zipcode, ZipcodeType
from .state_abbr import STATE_ABBR_SHORT_TO_LONG, STATE_ABBR_LONG_TO_SHORT
from .pkg.fuzzywuzzy.process import extract, extractOne

SORT_BY_DIST = "dist"
"""
a string for ``sort_by`` arguments. order the result by distance from a coordinates.
"""

DEFAULT_LIMIT = 5
"""
default number of results to return.
"""


class SearchEngine(object):
    """
    Zipcode Search Engine.

    :param simple_zipcode: bool, default True, if True, use the simple zipcode
        db. Rich Demographics, Real Estate, Employment, Education info is not
        available. If False, use the rich info database.

    Usage::

        >>> search = SearchEngine()
        >>> zipcode = search.by_zipcode("10001")

    Context Manager::

        >>> with SearchEngine() as search:
        ...     for zipcode in search.by_coordinates(lat, lng, radius):
        ...         # do what every you want


    :meth:`SearchEngine.query` provides mass options to customize your query.

    :attr:`SearchEngine.ses` is a ``sqlalchemy.orm.Session`` object, you can
    use it for query. For example::

        >>> from uszipcode import SearchEngine, SimpleZipcode
        >>> search = SearchEngine()
        >>> search.ses.query(SimpleZipcode).filter(SimpleZipcode.zipcode=="10001")

    .. note::

        :class:`SearchEngine` is not multi-thread safe. You should create different
        instance for each thread.
    """
    _city_list = None
    _state_list = None
    """
    all available state list, in long format 
    """
    _state_to_city_mapper = None
    _city_to_state_mapper = None

    def __init__(self, simple_zipcode=True):
        if simple_zipcode:
            if not is_simple_db_file_exists():
                download_simple_db_file()
            engine = connect_to_simple_zipcode_db()
            self.zip_klass = SimpleZipcode
        else:  # pragma: no cover
            if not is_db_file_exists():
                download_db_file()
            engine = connect_to_zipcode_db()
            self.zip_klass = Zipcode
        self.ses = sessionmaker(bind=engine)()

    def __enter__(self):  # pragma: no cover
        return self

    def __exit__(self, *exc_info):  # pragma: no cover
        self.close()

    def close(self):
        """
        close database connection.
        """
        self.ses.close()

    def _get_cache_data(self):
        self._city_list = set()
        self._state_list = list()
        self._state_to_city_mapper = dict()
        self._city_to_state_mapper = dict()

        for major_city, state in self.ses.query(self.zip_klass.major_city, self.zip_klass.state):
            if major_city is not None:
                self._city_list.add(major_city)

                if state is not None:
                    state = state.upper()
                    try:
                        self._state_to_city_mapper[state].append(major_city)
                    except:
                        self._state_to_city_mapper[state] = [major_city, ]

                    try:
                        self._city_to_state_mapper[major_city].append(state)
                    except:
                        self._city_to_state_mapper[major_city] = [state, ]

        self._city_list = list(self._city_list)
        self._city_list.sort()
        self._state_list = list(STATE_ABBR_LONG_TO_SHORT)
        self._state_list.sort()

        self._state_to_city_mapper = OrderedDict(
            sorted(
                self._state_to_city_mapper.items(),
                key=lambda x: x[0]
            )
        )
        for v in self._state_to_city_mapper.values():
            v.sort()

        self._city_to_state_mapper = OrderedDict(
            sorted(
                self._city_to_state_mapper.items(),
                key=lambda x: x[0]
            )
        )
        for v in self._city_to_state_mapper.values():
            v.sort()

    @property
    def city_list(self):  # pragma: no cover
        """
        Return all available city name.
        """
        if self._city_list is None:
            self._get_cache_data()
        return self._city_list

    @property
    def state_list(self):  # pragma: no cover
        """
        Return all available state name.
        """
        if self._state_list is None:
            self._get_cache_data()
        return self._state_list

    @property
    def state_to_city_mapper(self):  # pragma: no cover
        if self._state_to_city_mapper is None:
            self._get_cache_data()
        return self._state_to_city_mapper

    @property
    def city_to_state_mapper(self):  # pragma: no cover
        if self._city_to_state_mapper is None:
            self._get_cache_data()
        return self._city_to_state_mapper

    def find_state(self, state, best_match=True, min_similarity=70):
        """
        Fuzzy search correct state.

        :param best_match: bool, when True, only the best matched state
            will be return. otherwise, will return all matching states.
        """
        result_state_short_list = list()

        # check if it is a abbreviate name
        if state.upper() in STATE_ABBR_SHORT_TO_LONG:
            result_state_short_list.append(state.upper())

        # if not, find out what is the state that user looking for
        else:
            if best_match:
                state_long, confidence = extractOne(state, self.state_list)
                if confidence >= min_similarity:
                    result_state_short_list.append(
                        STATE_ABBR_LONG_TO_SHORT[state_long])
            else:
                for state_long, confidence in extract(state, self.state_list):
                    if confidence >= min_similarity:
                        result_state_short_list.append(
                            STATE_ABBR_LONG_TO_SHORT[state_long])

        if len(result_state_short_list) == 0:
            message = ("'%s' is not a valid state name, use 2 letter "
                       "short name or correct full name please.")
            raise ValueError(message % state)

        return result_state_short_list

    def find_city(self, city, state=None, best_match=True, min_similarity=70):
        """
        Fuzzy search correct city.

        :param city: city name.
        :param state: search city in specified state.
        :param best_match: bool, when True, only the best matched city
            will return. otherwise, will return all matching cities.

        **中文文档**

        如果给定了state, 则只在指定的state里的城市中寻找, 否则, 在全国所有的城市中寻找。
        """
        # find out what is the city that user looking for
        if state:
            state_sort = self.find_state(state, best_match=True)[0]
            city_pool = self.state_to_city_mapper[state_sort.upper()]
        else:
            city_pool = self.city_list

        result_city_list = list()

        if best_match:
            city, confidence = extractOne(city, city_pool)
            if confidence >= min_similarity:
                result_city_list.append(city)
        else:
            for city, confidence in extract(city, city_pool):
                if confidence >= min_similarity:
                    result_city_list.append(city)

        if len(result_city_list) == 0:
            raise ValueError("'%s' is not a valid city name" % city)

        return result_city_list

    @staticmethod
    def _resolve_sort_by(sort_by, flag_radius_query):
        """
        Result ``sort_by`` argument.

        :param sort_by: str, or sqlalchemy ORM attribute.
        :param flag_radius_query:
        :return:
        """
        if sort_by is None:
            if flag_radius_query:
                sort_by = SORT_BY_DIST
        elif isinstance(sort_by, string_types):
            if sort_by.lower() == SORT_BY_DIST:
                if flag_radius_query is False:
                    msg = "`sort_by` arg can be 'dist' only under distance based query!"
                    raise ValueError(msg)
                sort_by = SORT_BY_DIST
            elif sort_by not in SimpleZipcode.__table__.columns:
                msg = "`sort_by` arg has to be one of the Zipcode attribute or 'dist'!"
                raise ValueError(msg)
        else:
            sort_by = sort_by.name

        return sort_by

    def query(self,
              zipcode=None,
              prefix=None,
              pattern=None,
              city=None,
              state=None,
              lat=None,
              lng=None,
              radius=None,

              population_lower=None,
              population_upper=None,
              population_density_lower=None,
              population_density_upper=None,

              land_area_in_sqmi_lower=None,
              land_area_in_sqmi_upper=None,
              water_area_in_sqmi_lower=None,
              water_area_in_sqmi_upper=None,

              housing_units_lower=None,
              housing_units_upper=None,
              occupied_housing_units_lower=None,
              occupied_housing_units_upper=None,

              median_home_value_lower=None,
              median_home_value_upper=None,
              median_household_income_lower=None,
              median_household_income_upper=None,

              zipcode_type=ZipcodeType.Standard,
              sort_by=SimpleZipcode.zipcode.name,
              ascending=True,
              returns=DEFAULT_LIMIT):
        """
        Query zipcode the simple way.

        :param zipcode: int or str, find the exactly matched zipcode. Will be
            automatically zero padding to 5 digits
        :param prefix: str, zipcode prefix.
        :param pattern: str, zipcode wildcard.
        :param city: str, city name.
        :param state: str, state name, two letter abbr or state full name.
        :param lat: latitude.
        :param lng: longitude.
        :param radius: number, only returns zipcodes within a specific circle.
        :param population_lower:
        :param population_upper:
        :param population_density_lower:
        :param population_density_upper:
        :param land_area_in_sqmi_lower:
        :param land_area_in_sqmi_upper:
        :param water_area_in_sqmi_lower:
        :param water_area_in_sqmi_upper:
        :param housing_units_lower:
        :param housing_units_upper:
        :param occupied_housing_units_lower:
        :param occupied_housing_units_upper:
        :param median_home_value_lower:
        :param median_home_value_upper:
        :param median_household_income_lower:
        :param median_household_income_upper:
        :param zipcode_type: str or :class`~uszipcode.model.ZipcodeType` attribute.
            if None, allows to return any type of zipcode.
            if specified, only return specified zipcode type.
        :param sort_by: str or :class:`~uszipcode.model.Zipcode` attribute,
            specified which field is used for sorting.
        :param ascending: bool, True means ascending, False means descending.
        :param returns: int or None, limit the number of result to returns.

        :return: list of :class:`~uszipcode.model.SimpleZipcode` or
            :class:`~uszipcode.model.Zipcode`.
        """
        filters = list()

        # by coordinates
        _n_radius_param_not_null = sum([
            isinstance(lat, (integer_types, float)),
            isinstance(lng, (integer_types, float)),
            isinstance(radius, (integer_types, float)),
        ])
        if _n_radius_param_not_null == 3:
            flag_radius_query = True
            if radius <= 0:  # pragma: no cover
                raise ValueError("`radius` parameters can't less than 0!")
            elif radius <= 50:  # pragma: no cover
                radius_coef = 1.05
            elif radius <= 100:  # pragma: no cover
                radius_coef = 1.10
            elif radius <= 250:  # pragma: no cover
                radius_coef = 1.25
            elif radius <= 500:  # pragma: no cover
                radius_coef = 1.5
            else:  # pragma: no cover
                radius_coef = 2.0

            if radius >= 250:  # pragma: no cover
                msg = ("\nwarning! search within radius >= 250 miles "
                       "may greatly slow down the query!")
                sys.stdout.write(msg)

            # define lat lng boundary
            dist_btwn_lat_deg = 69.172
            dist_btwn_lon_deg = math.cos(lat) * 69.172
            lat_degr_rad = abs(radius * radius_coef / dist_btwn_lat_deg)
            lon_degr_rad = abs(radius * radius_coef / dist_btwn_lon_deg)

            lat_lower = lat - lat_degr_rad
            lat_upper = lat + lat_degr_rad
            lng_lower = lng - lon_degr_rad
            lng_upper = lng + lon_degr_rad

            filters.append(self.zip_klass.lat >= lat_lower)
            filters.append(self.zip_klass.lat <= lat_upper)
            filters.append(self.zip_klass.lng >= lng_lower)
            filters.append(self.zip_klass.lng <= lng_upper)
        elif _n_radius_param_not_null == 0:
            flag_radius_query = False
        else:
            msg = "You can either specify all of `lat`, `lng`, `radius` or none of them"
            raise ValueError(msg)

        # by city or state
        if (state is not None) and (city is not None):
            try:
                state = self.find_state(state, best_match=True)[0]
                city = self.find_city(city, state, best_match=True)[0]
                filters.append(self.zip_klass.state == state)
                filters.append(self.zip_klass.major_city == city)
            except ValueError:  # pragma: no cover
                return []
        elif (state is not None):
            try:
                state = self.find_state(state, best_match=True)[0]
                filters.append(self.zip_klass.state == state)
            except ValueError:  # pragma: no cover
                return []
        elif (city is not None):
            try:
                city = self.find_city(city, None, best_match=True)[0]
                filters.append(self.zip_klass.major_city == city)
            except ValueError:  # pragma: no cover
                return []
        else:
            pass

        # by common filter
        if sum([zipcode is None, prefix is None, pattern is None]) <= 1:
            msg = "You can only specify one of the `zipcode`, `prefix` and `pattern`!"
            raise ValueError(msg)

        if zipcode_type is not None:
            filters.append(self.zip_klass.zipcode_type == zipcode_type)

        if zipcode is not None:
            filters.append(self.zip_klass.zipcode == str(zipcode))
        if prefix is not None:
            filters.append(self.zip_klass.zipcode.startswith(str(prefix)))
        if pattern is not None:
            filters.append(self.zip_klass.zipcode.like(
                "%%%s%%" % str(pattern)))

        if population_lower is not None:
            filters.append(self.zip_klass.population >= population_lower)
        if population_upper is not None:
            filters.append(self.zip_klass.population <= population_upper)

        if population_density_lower is not None:
            filters.append(self.zip_klass.population_density >=
                           population_density_lower)
        if population_density_upper is not None:
            filters.append(self.zip_klass.population_density <=
                           population_density_upper)

        if land_area_in_sqmi_lower is not None:
            filters.append(self.zip_klass.land_area_in_sqmi >=
                           land_area_in_sqmi_lower)
        if land_area_in_sqmi_upper is not None:
            filters.append(self.zip_klass.land_area_in_sqmi <=
                           land_area_in_sqmi_upper)

        if water_area_in_sqmi_lower is not None:
            filters.append(self.zip_klass.water_area_in_sqmi >=
                           water_area_in_sqmi_lower)
        if water_area_in_sqmi_upper is not None:
            filters.append(self.zip_klass.water_area_in_sqmi <=
                           water_area_in_sqmi_upper)

        if housing_units_lower is not None:
            filters.append(self.zip_klass.housing_units >= housing_units_lower)
        if housing_units_upper is not None:
            filters.append(self.zip_klass.housing_units <= housing_units_upper)

        if occupied_housing_units_lower is not None:
            filters.append(self.zip_klass.occupied_housing_units >=
                           occupied_housing_units_lower)
        if occupied_housing_units_upper is not None:
            filters.append(self.zip_klass.occupied_housing_units <=
                           occupied_housing_units_upper)

        if median_home_value_lower is not None:
            filters.append(self.zip_klass.median_home_value >=
                           median_home_value_lower)
        if median_home_value_upper is not None:
            filters.append(self.zip_klass.median_home_value <=
                           median_home_value_upper)

        if median_household_income_lower is not None:
            filters.append(self.zip_klass.median_household_income >=
                           median_household_income_lower)
        if median_household_income_upper is not None:
            filters.append(self.zip_klass.median_household_income <=
                           median_household_income_upper)

        # --- solve coordinates and other search sort_by conflict ---
        sort_by = self._resolve_sort_by(sort_by, flag_radius_query)

        q = self.ses.query(self.zip_klass).filter(*filters)

        if sort_by is None:
            pass
        elif sort_by == SORT_BY_DIST:
            pass
        else:
            field = getattr(self.zip_klass, sort_by)
            if ascending:
                by = field.asc()
            else:
                by = field.desc()
            q = q.order_by(by)

        if flag_radius_query:
            # if we query by radius, then ignore returns limit before the
            # distance calculation, and then manually limit the returns
            pairs = list()
            for z in q:
                dist = z.dist_from(lat, lng)
                if dist <= radius:
                    pairs.append((dist, z))

            if sort_by == SORT_BY_DIST:
                if ascending:
                    if returns:
                        pairs_new = heapq.nsmallest(
                            returns, pairs, key=lambda x: x[0])
                    else:
                        pairs_new = list(sorted(pairs, key=lambda x: x[0]))
                else:
                    if returns:
                        pairs_new = heapq.nlargest(
                            returns, pairs, key=lambda x: x[0])
                    else:
                        pairs_new = list(
                            sorted(pairs, key=lambda x: x[0], reverse=True))
                return [z for _, z in pairs_new]
            else:
                return [z for _, z in pairs[:returns]]
        else:
            if returns:
                return q.limit(returns).all()
            else:
                return q.all()

    def by_zipcode(self,
                   zipcode,
                   zipcode_type=None,
                   zero_padding=True):
        """
        Search zipcode by exact 5 digits zipcode. No zero padding is needed.

        :param zipcode: int or str, the zipcode will be automatically
            zero padding to 5 digits.
        :param zipcode_type: str or :class`~uszipcode.model.ZipcodeType` attribute.
            by default, it returns any zipcode type.
        :param zero_padding: bool, toggle on and off automatic zero padding.
        """
        if zero_padding:
            zipcode = str(zipcode).zfill(5)
        else:  # pragma: no cover
            zipcode = str(zipcode)

        res = self.query(
            zipcode=zipcode,
            sort_by=None,
            returns=1,
            zipcode_type=zipcode_type,
        )
        if len(res):
            return res[0]
        else:
            return self.zip_klass()

    def by_prefix(self,
                  prefix,
                  zipcode_type=ZipcodeType.Standard,
                  sort_by=SimpleZipcode.zipcode.name,
                  ascending=True,
                  returns=DEFAULT_LIMIT):
        """
        Search zipcode information by first N digits.

        Returns multiple results.
        """
        return self.query(
            prefix=prefix,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_pattern(self,
                   pattern,
                   zipcode_type=ZipcodeType.Standard,
                   sort_by=SimpleZipcode.zipcode.name,
                   ascending=True,
                   returns=DEFAULT_LIMIT):
        """
        Search zipcode by wildcard.

        Returns multiple results.
        """
        return self.query(
            pattern=pattern,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_city(self,
                city,
                zipcode_type=ZipcodeType.Standard,
                sort_by=SimpleZipcode.zipcode.name,
                ascending=True,
                returns=DEFAULT_LIMIT):
        """
        Search zipcode information by fuzzy City name.

        My engine use fuzzy match and guess what is the city you want.
        """
        return self.query(
            city=city,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_state(self,
                 state,
                 zipcode_type=ZipcodeType.Standard,
                 sort_by=SimpleZipcode.zipcode.name,
                 ascending=True,
                 returns=DEFAULT_LIMIT):
        """
        Search zipcode information by fuzzy State name.

        My engine use fuzzy match and guess what is the state you want.
        """
        return self.query(
            state=state,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_city_and_state(self,
                          city,
                          state,
                          zipcode_type=ZipcodeType.Standard,
                          sort_by=SimpleZipcode.zipcode.name,
                          ascending=True,
                          returns=DEFAULT_LIMIT):
        """
        Search zipcode information by fuzzy city and state name.

        My engine use fuzzy match and guess what is the state you want.
        """
        return self.query(
            city=city,
            state=state,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_coordinates(self,
                       lat,
                       lng,
                       radius=25.0,
                       zipcode_type=ZipcodeType.Standard,
                       sort_by=SORT_BY_DIST,
                       ascending=True,
                       returns=DEFAULT_LIMIT):
        """
        Search zipcode information near a coordinates on a map.

        Returns multiple results.

        :param lat: center latitude.
        :param lng: center longitude.
        :param radius: only returns zipcode within X miles from ``lat``, ``lng``.

        **中文文档**

        1. 计算出在中心坐标处, 每一经度和纬度分别代表多少miles.
        2. 以给定坐标为中心, 画出一个矩形, 长宽分别为半径的2倍多一点, 找到该
          矩形内所有的Zipcode.
        3. 对这些Zipcode计算出他们的距离, 然后按照距离远近排序。距离超过我们
          限定的半径的直接丢弃.
        """
        return self.query(
            lat=lat, lng=lng, radius=radius,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_population(self,
                      lower=-1,
                      upper=2 ** 31,
                      zipcode_type=ZipcodeType.Standard,
                      sort_by=SimpleZipcode.population.name,
                      ascending=False,
                      returns=DEFAULT_LIMIT):
        """
        Search zipcode information by population range.
        """
        return self.query(
            population_lower=lower,
            population_upper=upper,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_population_density(self,
                              lower=-1,
                              upper=2 ** 31,
                              zipcode_type=ZipcodeType.Standard,
                              sort_by=SimpleZipcode.population_density.name,
                              ascending=False,
                              returns=DEFAULT_LIMIT):
        """
        Search zipcode information by population density range.

        `population density` is `population per square miles on land`
        """
        return self.query(
            population_density_lower=lower,
            population_density_upper=upper,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_land_area_in_sqmi(self,
                             lower=-1,
                             upper=2 ** 31,
                             zipcode_type=ZipcodeType.Standard,
                             sort_by=SimpleZipcode.land_area_in_sqmi.name,
                             ascending=False,
                             returns=DEFAULT_LIMIT):
        """
        Search zipcode information by land area / sq miles range.
        """
        return self.query(
            land_area_in_sqmi_lower=lower,
            land_area_in_sqmi_upper=upper,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_water_area_in_sqmi(self,
                              lower=-1,
                              upper=2 ** 31,
                              zipcode_type=ZipcodeType.Standard,
                              sort_by=SimpleZipcode.water_area_in_sqmi.name,
                              ascending=False,
                              returns=DEFAULT_LIMIT):
        """
        Search zipcode information by water area / sq miles range.
        """
        return self.query(
            water_area_in_sqmi_lower=lower,
            water_area_in_sqmi_upper=upper,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_housing_units(self,
                         lower=-1,
                         upper=2 ** 31,
                         zipcode_type=ZipcodeType.Standard,
                         sort_by=SimpleZipcode.housing_units.name,
                         ascending=False,
                         returns=DEFAULT_LIMIT):
        """
        Search zipcode information by house of units.
        """
        return self.query(
            housing_units_lower=lower,
            housing_units_upper=upper,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_occupied_housing_units(self,
                                  lower=-1,
                                  upper=2 ** 31,
                                  zipcode_type=ZipcodeType.Standard,
                                  sort_by=SimpleZipcode.occupied_housing_units.name,
                                  ascending=False,
                                  returns=DEFAULT_LIMIT):
        """
        Search zipcode information by occupied house of units.
        """
        return self.query(
            occupied_housing_units_lower=lower,
            occupied_housing_units_upper=upper,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_median_home_value(self,
                             lower=-1,
                             upper=2 ** 31,
                             zipcode_type=ZipcodeType.Standard,
                             sort_by=SimpleZipcode.median_home_value.name,
                             ascending=False,
                             returns=DEFAULT_LIMIT):
        """
        Search zipcode information by median home value.
        """
        return self.query(
            median_home_value_lower=lower,
            median_home_value_upper=upper,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_median_household_income(self,
                                   lower=-1,
                                   upper=2 ** 31,
                                   zipcode_type=ZipcodeType.Standard,
                                   sort_by=SimpleZipcode.median_household_income.name,
                                   ascending=False,
                                   returns=DEFAULT_LIMIT):
        """
        Search zipcode information by median household income.
        """
        return self.query(
            median_household_income_lower=lower,
            median_household_income_upper=upper,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )
