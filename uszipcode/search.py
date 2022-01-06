# -*- coding: utf-8 -*-

"""
This module allows developer to query zipcode with super clean API.
"""

import sys
import math
import enum
import heapq
import typing
from collections import OrderedDict

import sqlalchemy as sa
from sqlalchemy.engine import Engine
import sqlalchemy.orm as orm
import sqlalchemy_mate as sam
from pathlib_mate import Path
from fuzzywuzzy.process import extract, extractOne

from .db import (
    download_db_file,
    DEFAULT_SIMPLE_DB_FILE_PATH, DEFAULT_COMPREHENSIVE_DB_FILE_PATH,
    SIMPLE_DB_FILE_DOWNLOAD_URL, COMPREHENSIVE_DB_FILE_DOWNLOAD_URL,
)
from .model import ZipcodeTypeEnum, SimpleZipcode, ComprehensiveZipcode
from .state_abbr import (
    MAPPER_STATE_ABBR_SHORT_TO_LONG, MAPPER_STATE_ABBR_LONG_TO_SHORT,
)

SORT_BY_DIST = "dist"
"""
a string for ``sort_by`` arguments. order the result by distance from a coordinates.
"""

DEFAULT_LIMIT = 5
"""
default number of results to return.
"""

HOME = Path.home().abspath
HOME_USZIPCODE = Path(HOME, ".uszipcode").abspath


def validate_enum_arg(
    enum_class: typing.Type[enum.Enum],
    attr: str,
    value: enum.Enum,
):
    if not isinstance(value, enum_class):
        raise TypeError(
            (
                "param '{}' validation error: "
                "'{}' is not a valid {} type!"
            ).format(attr, value, enum_class)
        )

    if value not in enum_class:  # pragma: no cover
        raise ValueError(
            (
                "param '{}' validation error: "
                "'{}' is not a valid {} value!"
            ).format(attr, value, enum_class)
        )


class SearchEngine(object):
    """
    Zipcode Search Engine.

    :type simple_or_comprehensive: SearchEngine.SimpleOrComprehensiveArgEnum
    :param simple_or_comprehensive: default SearchEngine.SimpleOrComprehensiveArgEnum,
        use the simple zipcode db. Rich Demographics, Real Estate, Employment,
        Education info are not available. if
        SearchEngine.SimpleOrComprehensiveArgEnum.comprehensive,
        use the rich info database.

    :type db_file_path: str
    :param db_file_path: where you want to download the sqlite database to. This
        property allows you to customize where you want to store the data file
        locally. by default it is ${HOME}/.uszipcode/...

    :type download_url: str
    :param download_url: where you want to download the sqlite database file from.
        This property allows you to upload the .sqlite file to your private file
        host and download from it. In case the default download url fail.

    :type engine: Engine
    :param engine: a sqlachemy engine object. It allows you to use any
        backend database instead of the default sqlite database.

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

        >>> from uszipcode import SearchEngine, SimpleZipcode, ComprehensiveZipcode
        >>> search = SearchEngine()
        >>> search.ses.scalar(SimpleZipcode).filter(SimpleZipcode.zipcode=="10001")

    .. note::

        :class:`SearchEngine` is not multi-thread safe. You should create different
        instance for each thread.
    """

    class SimpleOrComprehensiveArgEnum(enum.Enum):
        simple = enum.auto()
        comprehensive = enum.auto()

    _default_db_file_path_mapper = {
        SimpleOrComprehensiveArgEnum.simple: DEFAULT_SIMPLE_DB_FILE_PATH,
        SimpleOrComprehensiveArgEnum.comprehensive: DEFAULT_COMPREHENSIVE_DB_FILE_PATH,
    }
    _default_download_url_mapper = {
        SimpleOrComprehensiveArgEnum.simple: SIMPLE_DB_FILE_DOWNLOAD_URL,
        SimpleOrComprehensiveArgEnum.comprehensive: COMPREHENSIVE_DB_FILE_DOWNLOAD_URL,
    }

    def __init__(
        self,
        simple_or_comprehensive: SimpleOrComprehensiveArgEnum = SimpleOrComprehensiveArgEnum.simple,
        db_file_path: typing.Union[str, None] = None,
        download_url: typing.Union[str, None] = None,
        engine: Engine = None,
    ):
        validate_enum_arg(
            self.SimpleOrComprehensiveArgEnum,
            "simple_or_comprehensive",
            simple_or_comprehensive,
        )
        self.simple_or_comprehensive = simple_or_comprehensive

        if isinstance(engine, Engine):
            self.db_file_path = None
            self.download_url = None
            self.engine = engine
        else:
            self.db_file_path = db_file_path
            self.download_url = download_url
            self._download_db_file_if_not_exists()
            self.engine = sam.EngineCreator().create_sqlite(path=self.db_file_path)
        self.eng = self.engine
        self.session = orm.Session(self.engine)
        self.ses = self.session

        self.zip_klass: typing.Union[SimpleZipcode, ComprehensiveZipcode]
        if self.simple_or_comprehensive is self.SimpleOrComprehensiveArgEnum.simple:
            self.zip_klass = SimpleZipcode
        elif self.simple_or_comprehensive is self.SimpleOrComprehensiveArgEnum.comprehensive:
            self.zip_klass = ComprehensiveZipcode

    def _download_db_file_if_not_exists(self):
        if self.db_file_path is None:
            self.db_file_path = self._default_db_file_path_mapper[self.simple_or_comprehensive]
        if self.download_url is None:
            self.download_url = self._default_download_url_mapper[self.simple_or_comprehensive]
        p = Path(self.db_file_path)
        if not p.exists():
            if self.simple_or_comprehensive is self.SimpleOrComprehensiveArgEnum.simple:
                download_db_file(
                    db_file_path=self.db_file_path,
                    download_url=self.download_url,
                    chunk_size=1024 * 1024,
                    progress_size=1024 * 1024,
                )
            elif self.simple_or_comprehensive is self.SimpleOrComprehensiveArgEnum.comprehensive:
                download_db_file(
                    db_file_path=self.db_file_path,
                    download_url=self.download_url,
                    chunk_size=1024 * 1024,
                    progress_size=50 * 1024 * 1024,
                )

    def __enter__(self):  # pragma: no cover
        return self

    def __exit__(self, *exc_info):  # pragma: no cover
        self.close()

    def __del__(self):  # pragma: no cover
        # Cleanup connection if still open
        if self.ses:
            self.close()

    def close(self):
        """
        close database connection.
        """
        self.ses.close()

    # Since fuzzy search on City and State requires full list of city and state
    # We load the full list from the database only once and store it in cache
    _city_list: typing.List[str] = None
    """
    all available city list
    """

    _state_list: typing.List[str] = None
    """
    all available state list, in long format 
    """

    _state_to_city_mapper: typing.Dict[str, list] = None
    """
    
    """

    _city_to_state_mapper: typing.Dict[str, list] = None

    def _get_cache_data(self):
        _city_set = set()
        _state_to_city_mapper: typing.Dict[str, set] = dict()
        _city_to_state_mapper: typing.Dict[str, set] = dict()

        stmt = sa.select(self.zip_klass.major_city, self.zip_klass.state)
        for major_city, state in self.ses.execute(stmt):
            if major_city is not None:
                _city_set.add(major_city)
                if state is not None:
                    state = state.upper()
                    try:
                        _state_to_city_mapper[state].add(major_city)
                    except:
                        _state_to_city_mapper[state] = {major_city, }

                    try:
                        _city_to_state_mapper[major_city].add(state)
                    except:
                        _city_to_state_mapper[major_city] = {state, }

        self._city_list = list(_city_set)
        self._city_list.sort()
        self._state_list = list(MAPPER_STATE_ABBR_LONG_TO_SHORT)
        self._state_list.sort()

        self._state_to_city_mapper = OrderedDict(
            sorted(
                (
                    (state, list(city_set))
                    for state, city_set in _state_to_city_mapper.items()
                ),
                key=lambda x: x[0]
            )
        )
        for city_list in self._state_to_city_mapper.values():
            city_list.sort()

        self._city_to_state_mapper = OrderedDict(
            sorted(
                (
                    (city, list(state_set))
                    for city, state_set in _city_to_state_mapper.items()
                ),
                key=lambda x: x[0]
            )
        )
        for state_list in self._city_to_state_mapper.values():
            state_list.sort()

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

    def find_state(
        self,
        state: str,
        best_match: bool = True,
        min_similarity: int = 70,
    ) -> typing.List[str]:
        """
        Fuzzy search correct state.

        :param best_match: bool, when True, only the best matched state
            will be return. otherwise, will return all matching states.
        """
        result_state_short_list = list()

        # check if it is a abbreviate name
        if state.upper() in MAPPER_STATE_ABBR_SHORT_TO_LONG:
            result_state_short_list.append(state.upper())

        # if not, find out what is the state that user looking for
        else:
            if best_match:
                state_long, confidence = extractOne(state, self.state_list)
                if confidence >= min_similarity:
                    result_state_short_list.append(
                        MAPPER_STATE_ABBR_LONG_TO_SHORT[state_long])
            else:
                for state_long, confidence in extract(state, self.state_list):
                    if confidence >= min_similarity:
                        result_state_short_list.append(
                            MAPPER_STATE_ABBR_LONG_TO_SHORT[state_long])

        if len(result_state_short_list) == 0:
            message = ("'%s' is not a valid state name, use 2 letter "
                       "short name or correct full name please.")
            raise ValueError(message % state)

        return result_state_short_list

    def find_city(
        self,
        city: str,
        state: str = None,
        best_match: bool = True,
        min_similarity: int = 70,
    ) -> typing.List[str]:
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
            state_short = self.find_state(state, best_match=True)[0]
            city_pool = self.state_to_city_mapper[state_short.upper()]
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
    def _resolve_sort_by(sort_by: str, flag_radius_query: bool):
        """
        Result ``sort_by`` argument.

        :param sort_by: str, or sqlalchemy ORM attribute.
        :param flag_radius_query:
        :return:
        """
        if sort_by is None:
            if flag_radius_query:
                sort_by = SORT_BY_DIST
        elif isinstance(sort_by, str):
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

    def query(
        self,
        zipcode: typing.Union[int, float] = None,
        prefix: str = None,
        pattern: str = None,
        city: str = None,
        state: str = None,
        lat: typing.Union[int, float] = None,
        lng: typing.Union[int, float] = None,
        radius=None,

        population_lower: int = None,
        population_upper: int = None,
        population_density_lower: int = None,
        population_density_upper: int = None,

        land_area_in_sqmi_lower: int = None,
        land_area_in_sqmi_upper: int = None,
        water_area_in_sqmi_lower: int = None,
        water_area_in_sqmi_upper: int = None,

        housing_units_lower: int = None,
        housing_units_upper: int = None,
        occupied_housing_units_lower: int = None,
        occupied_housing_units_upper: int = None,

        median_home_value_lower: int = None,
        median_home_value_upper: int = None,
        median_household_income_lower: int = None,
        median_household_income_upper: int = None,

        zipcode_type: ZipcodeTypeEnum = ZipcodeTypeEnum.Standard,
        sort_by: str = SimpleZipcode.zipcode.name,
        ascending: bool = True,
        returns: int = DEFAULT_LIMIT,
    ):
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
            :class:`~uszipcode.model.ComprehensiveZipcode`.
        """
        filters = list()

        # by coordinates
        _n_radius_param_not_null = sum([
            isinstance(lat, (int, float)),
            isinstance(lng, (int, float)),
            isinstance(radius, (int, float)),
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

            # define lat lng boundary, should be slightly larger than the circle
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
            state = self.find_state(state, best_match=True)[0]
            city = self.find_city(city, state, best_match=True)[0]
            filters.append(self.zip_klass.state == state)
            filters.append(self.zip_klass.major_city == city)
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
            filters.append(self.zip_klass.zipcode_type == zipcode_type.value)
        if zipcode is not None:
            filters.append(self.zip_klass.zipcode == str(zipcode))
        if prefix is not None:
            filters.append(self.zip_klass.zipcode.startswith(str(prefix)))
        if pattern is not None:
            filters.append(
                self.zip_klass.zipcode.like("%%%s%%" % str(pattern))
            )

        if population_lower is not None:
            filters.append(self.zip_klass.population >= population_lower)
        if population_upper is not None:
            filters.append(self.zip_klass.population <= population_upper)

        if population_density_lower is not None:
            filters.append(
                self.zip_klass.population_density >= population_density_lower
            )
        if population_density_upper is not None:
            filters.append(
                self.zip_klass.population_density <= population_density_upper
            )

        if land_area_in_sqmi_lower is not None:
            filters.append(
                self.zip_klass.land_area_in_sqmi >= land_area_in_sqmi_lower
            )
        if land_area_in_sqmi_upper is not None:
            filters.append(
                self.zip_klass.land_area_in_sqmi <= land_area_in_sqmi_upper
            )

        if water_area_in_sqmi_lower is not None:
            filters.append(
                self.zip_klass.water_area_in_sqmi >= water_area_in_sqmi_lower
            )
        if water_area_in_sqmi_upper is not None:
            filters.append(
                self.zip_klass.water_area_in_sqmi <= water_area_in_sqmi_upper
            )

        if housing_units_lower is not None:
            filters.append(self.zip_klass.housing_units >= housing_units_lower)
        if housing_units_upper is not None:
            filters.append(self.zip_klass.housing_units <= housing_units_upper)

        if occupied_housing_units_lower is not None:
            filters.append(
                self.zip_klass.occupied_housing_units >= occupied_housing_units_lower
            )
        if occupied_housing_units_upper is not None:
            filters.append(
                self.zip_klass.occupied_housing_units <= occupied_housing_units_upper
            )

        if median_home_value_lower is not None:
            filters.append(
                self.zip_klass.median_home_value >= median_home_value_lower
            )
        if median_home_value_upper is not None:
            filters.append(
                self.zip_klass.median_home_value <= median_home_value_upper
            )

        if median_household_income_lower is not None:
            filters.append(
                self.zip_klass.median_household_income >= median_household_income_lower
            )
        if median_household_income_upper is not None:
            filters.append(
                self.zip_klass.median_household_income <= median_household_income_upper
            )

        # --- solve coordinates and other search sort_by conflict ---
        sort_by = self._resolve_sort_by(sort_by, flag_radius_query)

        stmt = sa.select(self.zip_klass).where(*filters)

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
            stmt = stmt.order_by(by)

        if flag_radius_query:
            # if we query by radius, then ignore returns limit before the
            # distance calculation, and then manually limit the returns
            pairs = list()
            for z in self.ses.scalars(stmt):
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
                            returns, pairs, key=lambda x: x[0]
                        )
                    else:
                        pairs_new = list(
                            sorted(pairs, key=lambda x: x[0], reverse=True)
                        )
                return [z for _, z in pairs_new]
            else:
                return [z for _, z in pairs[:returns]]
        else:
            if returns:
                stmt = stmt.limit(returns)

            return self.ses.scalars(stmt).all()

    def by_zipcode(
        self,
        zipcode: typing.Union[int, str],
        zero_padding: bool = True,
    ) -> typing.Union[SimpleZipcode, ComprehensiveZipcode, None]:
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
        return self.ses.get(self.zip_klass, zipcode)

    def by_prefix(
        self,
        prefix: str,
        zipcode_type: ZipcodeTypeEnum = ZipcodeTypeEnum.Standard,
        sort_by: str = SimpleZipcode.zipcode.name,
        ascending: bool = True,
        returns: int = DEFAULT_LIMIT,
    ):
        """
        Search zipcode information by first N digits.

        Returns multiple results.
        """
        return self.query(
            prefix=prefix,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_pattern(
        self,
        pattern: str,
        zipcode_type: ZipcodeTypeEnum = ZipcodeTypeEnum.Standard,
        sort_by: str = SimpleZipcode.zipcode.name,
        ascending: bool = True,
        returns: int = DEFAULT_LIMIT,
    ):
        """
        Search zipcode by wildcard.

        Returns multiple results.
        """
        return self.query(
            pattern=pattern,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_city(
        self,
        city: str,
        zipcode_type: ZipcodeTypeEnum = ZipcodeTypeEnum.Standard,
        sort_by: str = SimpleZipcode.zipcode.name,
        ascending: bool = True,
        returns: int = DEFAULT_LIMIT,
    ):
        """
        Search zipcode information by fuzzy City name.

        My engine use fuzzy match and guess what is the city you want.
        """
        return self.query(
            city=city,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_state(
        self,
        state: str,
        zipcode_type: ZipcodeTypeEnum = ZipcodeTypeEnum.Standard,
        sort_by: str = SimpleZipcode.zipcode.name,
        ascending: bool = True,
        returns: int = DEFAULT_LIMIT,
    ):
        """
        Search zipcode information by fuzzy State name.

        My engine use fuzzy match and guess what is the state you want.
        """
        return self.query(
            state=state,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_city_and_state(
        self,
        city: str,
        state: str,
        zipcode_type: ZipcodeTypeEnum = ZipcodeTypeEnum.Standard,
        sort_by: str = SimpleZipcode.zipcode.name,
        ascending: bool = True,
        returns: int = DEFAULT_LIMIT,
    ):
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

    def by_coordinates(
        self,
        lat: typing.Union[int, float],
        lng: typing.Union[int, float],
        radius: typing.Union[int, float] = 25.0,
        zipcode_type: ZipcodeTypeEnum = ZipcodeTypeEnum.Standard,
        sort_by: str = SORT_BY_DIST,
        ascending: bool = True,
        returns: int = DEFAULT_LIMIT,
    ):
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

    def by_population(
        self,
        lower: int = -1,
        upper: int = 2 ** 31,
        zipcode_type: ZipcodeTypeEnum = ZipcodeTypeEnum.Standard,
        sort_by: str = SimpleZipcode.population.name,
        ascending: bool = False,
        returns: int = DEFAULT_LIMIT,
    ):
        """
        Search zipcode information by population range.
        """
        return self.query(
            population_lower=lower,
            population_upper=upper,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_population_density(
        self,
        lower: int = -1,
        upper: int = 2 ** 31,
        zipcode_type: ZipcodeTypeEnum = ZipcodeTypeEnum.Standard,
        sort_by: str = SimpleZipcode.population_density.name,
        ascending: bool = False,
        returns: int = DEFAULT_LIMIT,
    ):
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

    def by_land_area_in_sqmi(
        self,
        lower: int = -1,
        upper: int = 2 ** 31,
        zipcode_type: ZipcodeTypeEnum = ZipcodeTypeEnum.Standard,
        sort_by: str = SimpleZipcode.land_area_in_sqmi.name,
        ascending: bool = False,
        returns: int = DEFAULT_LIMIT,
    ):
        """
        Search zipcode information by land area / sq miles range.
        """
        return self.query(
            land_area_in_sqmi_lower=lower,
            land_area_in_sqmi_upper=upper,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_water_area_in_sqmi(
        self,
        lower: int = -1,
        upper: int = 2 ** 31,
        zipcode_type: ZipcodeTypeEnum = ZipcodeTypeEnum.Standard,
        sort_by: str = SimpleZipcode.water_area_in_sqmi.name,
        ascending: bool = False,
        returns: int = DEFAULT_LIMIT,
    ):
        """
        Search zipcode information by water area / sq miles range.
        """
        return self.query(
            water_area_in_sqmi_lower=lower,
            water_area_in_sqmi_upper=upper,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_housing_units(
        self,
        lower: int = -1,
        upper: int = 2 ** 31,
        zipcode_type: ZipcodeTypeEnum = ZipcodeTypeEnum.Standard,
        sort_by: str = SimpleZipcode.housing_units.name,
        ascending: bool = False,
        returns: int = DEFAULT_LIMIT,
    ):
        """
        Search zipcode information by house of units.
        """
        return self.query(
            housing_units_lower=lower,
            housing_units_upper=upper,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_occupied_housing_units(
        self,
        lower: int = -1,
        upper: int = 2 ** 31,
        zipcode_type: ZipcodeTypeEnum = ZipcodeTypeEnum.Standard,
        sort_by: str = SimpleZipcode.occupied_housing_units.name,
        ascending: bool = False,
        returns: int = DEFAULT_LIMIT,
    ):
        """
        Search zipcode information by occupied house of units.
        """
        return self.query(
            occupied_housing_units_lower=lower,
            occupied_housing_units_upper=upper,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_median_home_value(
        self,
        lower: int = -1,
        upper: int = 2 ** 31,
        zipcode_type: ZipcodeTypeEnum = ZipcodeTypeEnum.Standard,
        sort_by: str = SimpleZipcode.median_home_value.name,
        ascending: bool = False,
        returns: int = DEFAULT_LIMIT,
    ):
        """
        Search zipcode information by median home value.
        """
        return self.query(
            median_home_value_lower=lower,
            median_home_value_upper=upper,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def by_median_household_income(
        self,
        lower: int = -1,
        upper: int = 2 ** 31,
        zipcode_type: ZipcodeTypeEnum = ZipcodeTypeEnum.Standard,
        sort_by: str = SimpleZipcode.median_household_income.name,
        ascending: bool = False,
        returns: int = DEFAULT_LIMIT,
    ):
        """
        Search zipcode information by median household income.
        """
        return self.query(
            median_household_income_lower=lower,
            median_household_income_upper=upper,
            sort_by=sort_by, zipcode_type=zipcode_type,
            ascending=ascending, returns=returns,
        )

    def inspect_raw_data(self, zipcode: str):
        sql = "SELECT * FROM {} WHERE zipcode = '{}'".format(
            self.zip_klass.__tablename__,
            str(zipcode).zfill(5),
        )
        stmt = sa.text(sql)
        return dict(self.engine.execute(stmt).fetchone())
