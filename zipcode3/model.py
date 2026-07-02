# -*- coding: utf-8 -*-

import json
import enum
import typing
from functools import total_ordering
from pathlib_mate import Path
import sqlalchemy as sa
import sqlalchemy.orm as orm
import sqlalchemy_mate as sam
from sqlalchemy_mate import api
from sqlalchemy_mate.types import api as types_api
from .state_abbr import (
    MAPPER_STATE_ABBR_SHORT_TO_LONG,
)
from haversine import haversine, Unit

Base = orm.declarative_base()


class ZipcodeTypeEnum(enum.Enum):
    """
    zipcode type visitor class.
    """
    Standard = "STANDARD"
    PO_Box = "PO BOX"
    Unique = "UNIQUE"
    Military = "MILITARY"


@total_ordering
class AbstractSimpleZipcode(Base, api.ExtendedBase):
    """
    Base class for Zipcode.
    """
    __abstract__ = True

    zipcode = sa.Column(sa.String, primary_key=True)
    zipcode_type = sa.Column(sa.String)
    major_city = sa.Column(sa.String)
    post_office_city = sa.Column(sa.String)
    common_city_list = sa.Column(types_api.CompressedJSONType)
    county = sa.Column(sa.String)
    state = sa.Column(sa.String)

    lat = sa.Column(sa.Float, index=True)
    lng = sa.Column(sa.Float, index=True)

    timezone = sa.Column(sa.String)
    radius_in_miles = sa.Column(sa.Float)
    area_code_list = sa.Column(types_api.CompressedJSONType)

    population = sa.Column(sa.Integer)
    population_density = sa.Column(sa.Float)

    land_area_in_sqmi = sa.Column(sa.Float)
    water_area_in_sqmi = sa.Column(sa.Float)

    housing_units = sa.Column(sa.Integer)
    occupied_housing_units = sa.Column(sa.Integer)

    median_home_value = sa.Column(sa.Integer)
    median_household_income = sa.Column(sa.Integer)

    bounds_west = sa.Column(sa.Float)
    bounds_east = sa.Column(sa.Float)
    bounds_north = sa.Column(sa.Float)
    bounds_south = sa.Column(sa.Float)

    _settings_major_attrs = "zipcode,zipcode_type,city,county,state,lat,lng,timezone".split(
        ",")

    @property
    def city(self):
        """
        Alias of ``.major_city``.
        """
        return self.major_city

    @property
    def bounds(self) -> dict:
        """
        Border boundary.
        """
        return {
            "west": self.bounds_west,
            "east": self.bounds_east,
            "north": self.bounds_north,
            "south": self.bounds_south,
        }

    @property
    def state_abbr(self) -> str:
        """
        Return state abbreviation, two letters, all uppercase.
        """
        return self.state.upper()

    @property
    def state_long(self) -> str:
        """
        Return state full name.
        """
        return MAPPER_STATE_ABBR_SHORT_TO_LONG.get(self.state.upper())

    def __bool__(self):
        """
        For Python3 bool() method.
        """
        return self.zipcode is not None

    def __lt__(self, other: 'AbstractSimpleZipcode'):
        """
        For ``>`` comparison operator.
        """
        if (self.zipcode is None) or (other.zipcode is None):
            raise ValueError(
                "Empty Zipcode instance doesn't support comparison.")
        else:
            return self.zipcode < other.zipcode

    def __eq__(self, other: 'AbstractSimpleZipcode'):
        """
        For ``==`` comparison operator.
        """
        return self.zipcode == other.zipcode

    def __hash__(self):
        """
        For hash() method
        """
        return hash(self.zipcode)

    def dist_from(self, lat: float, lng: float, unit: Unit = Unit.MILES):
        """
        Calculate the distance of the center of this zipcode from a coordinator.

        :param lat: latitude.
        :param lng: longitude.
        """
        return haversine((self.lat, self.lng), (lat, lng), unit=unit)

    def to_json(self, include_null: bool = True):
        """
        Convert to json.
        """
        data = self.to_OrderedDict(include_null=include_null)
        return json.dumps(data, indent=4)


class AbstractComprehensiveZipcode(AbstractSimpleZipcode):
    __abstract__ = True

    polygon = sa.Column(types_api.CompressedJSONType)

    # Stats and Demographics
    population_by_year = sa.Column(types_api.CompressedJSONType)
    population_by_age = sa.Column(types_api.CompressedJSONType)
    population_by_gender = sa.Column(types_api.CompressedJSONType)
    population_by_race = sa.Column(types_api.CompressedJSONType)
    head_of_household_by_age = sa.Column(types_api.CompressedJSONType)
    families_vs_singles = sa.Column(types_api.CompressedJSONType)
    households_with_kids = sa.Column(types_api.CompressedJSONType)
    children_by_age = sa.Column(types_api.CompressedJSONType)

    # Real Estate and Housing
    housing_type = sa.Column(types_api.CompressedJSONType)
    year_housing_was_built = sa.Column(types_api.CompressedJSONType)
    housing_occupancy = sa.Column(types_api.CompressedJSONType)
    vacancy_reason = sa.Column(types_api.CompressedJSONType)
    owner_occupied_home_values = sa.Column(types_api.CompressedJSONType)
    rental_properties_by_number_of_rooms = sa.Column(types_api.CompressedJSONType)

    monthly_rent_including_utilities_studio_apt = sa.Column(types_api.CompressedJSONType)
    monthly_rent_including_utilities_1_b = sa.Column(types_api.CompressedJSONType)
    monthly_rent_including_utilities_2_b = sa.Column(types_api.CompressedJSONType)
    monthly_rent_including_utilities_3plus_b = sa.Column(types_api.CompressedJSONType)

    # Employment, Income, Earnings, and Work
    employment_status = sa.Column(types_api.CompressedJSONType)
    average_household_income_over_time = sa.Column(types_api.CompressedJSONType)
    household_income = sa.Column(types_api.CompressedJSONType)
    annual_individual_earnings = sa.Column(types_api.CompressedJSONType)

    sources_of_household_income____percent_of_households_receiving_income = sa.Column(
        types_api.CompressedJSONType)
    sources_of_household_income____average_income_per_household_by_income_source = sa.Column(
        types_api.CompressedJSONType)

    household_investment_income____percent_of_households_receiving_investment_income = sa.Column(
        types_api.CompressedJSONType)
    household_investment_income____average_income_per_household_by_income_source = sa.Column(
        types_api.CompressedJSONType)

    household_retirement_income____percent_of_households_receiving_retirement_incom = sa.Column(
        types_api.CompressedJSONType)
    household_retirement_income____average_income_per_household_by_income_source = sa.Column(
        types_api.CompressedJSONType)

    source_of_earnings = sa.Column(types_api.CompressedJSONType)
    means_of_transportation_to_work_for_workers_16_and_over = sa.Column(
        types_api.CompressedJSONType)
    travel_time_to_work_in_minutes = sa.Column(sam.types.api.CompressedJSONType)

    # Schools and Education
    educational_attainment_for_population_25_and_over = sa.Column(
        types_api.CompressedJSONType)
    school_enrollment_age_3_to_17 = sa.Column(types_api.CompressedJSONType)


class SimpleZipcode(AbstractSimpleZipcode):
    __tablename__ = "simple_zipcode"


class ComprehensiveZipcode(AbstractComprehensiveZipcode):
    __tablename__ = "comprehensive_zipcode"
