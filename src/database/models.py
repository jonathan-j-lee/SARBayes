"""
database.models
===============
"""

__all__ = ['Subject', 'Group', 'Point', 'Location', 'Operation', 'Outcome',
           'Weather', 'Search', 'Incident']

import numbers
import re

from sqlalchemy import Integer, SmallInteger, Float, Boolean
from sqlalchemy import DateTime, Interval, Text, PickleType, Column, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import and_, not_, select, func
from sqlalchemy.orm import column_property, relationship, validates

from . import Base


class Subject(Base):
    __tablename__ = 'subjects'
    SEX_CODES = {0: 'unknown', 1: 'male', 2: 'female', 9: 'not_applicable'}
    DOA_TYPES = ['DOA', 'Suspended']

    id = Column(Integer, primary_key=True)
    age = Column(Float)  # Measured in years
    sex = Column(SmallInteger)  # See ISO/IEC 5218
    weight = Column(Float)  # Measured in kg
    height = Column(Float)  # Measured in cm
    physical_fit = Column(Text)
    mental_fit = Column(Text)
    personality = Column(Text)
    experience = Column(Text)
    training = Column(Text)
    equipment = Column(Text)
    clothing = Column(Text)
    status = Column(Text)
    group_id = Column(Integer, ForeignKey('groups.id'))
    group = relationship('Group', back_populates='subjects')

    @property
    def sex_as_str(self):
        return self.__class__.SEX_CODES.get(self.sex, None)

    dead_on_arrival = column_property(func.upper(status)
                                      .in_(map(str.upper, DOA_TYPES)))
    survived = column_property(not_(func.upper(status)
                                      .in_(map(str.upper, DOA_TYPES))))
    bmi = column_property(weight/height/height*1e4)  # Measured in kg/m^2

    @validates('age', 'weight', 'height')
    def validate_sign(self, key, value):
        if value is None or value >= 0:  # Possibly rounded down
            return value
        else:
            raise ValueError("'{}' must be a positive number".format(key))

    @validates('sex')
    def validate_sex_code(self, key, value):
        if value is None:
            return value
        for code, sex in self.__class__.SEX_CODES.items():
            if value == code:
                return value
            elif value == sex:
                return code
        else:
            raise ValueError("invalid code for '{}'".format(key))


class Group(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True)
    category = Column(Text)
    subcategory = Column(Text)
    activity = Column(Text)
    contact_method = Column(Text)
    scenario = Column(Text)
    detectability = Column(Text)
    mobile = Column(Boolean)
    responsive = Column(Boolean)
    lost_strategy = Column(Text)
    mobile_hours = Column(Interval)
    mechanism = Column(Text)
    injury_type = Column(Text)
    illness_type = Column(Text)
    treatment = Column(Text)
    rescue_method = Column(Text)
    signaling = Column(Text)
    subjects = relationship('Subject', back_populates='group',
                            cascade='all, delete-orphan')
    incident_id = Column(Integer, ForeignKey('incidents.id'))
    incident = relationship('Incident', back_populates='group', uselist=False)

    size = column_property(select([func.count(Subject.id)])
                           .where(Subject.group_id == id)
                           .correlate_except(Subject))


class Point(Base):
    __tablename__ = 'points'
    MIN_LATITUDE, MAX_LATITUDE = -90, 90
    MIN_LONGITUDE, MAX_LONGITUDE = -180, 180

    id = Column(Integer, primary_key=True)
    latitude = Column(Float)  # Measured in decimal degrees
    longitude = Column(Float)  # Measured in decimal degrees
    altitude = Column(Float)  # Measured in m above mean sea level

    @validates('latitude', 'longitude')
    def validate_bounds(self, key, value):
        cls = self.__class__
        if key == 'latitude':
            lowerbound, upperbound = cls.MIN_LATITUDE, cls.MAX_LATITUDE
        else:
            lowerbound, upperbound = cls.MIN_LONGITUDE, cls.MAX_LONGITUDE

        if value is None or lowerbound <= value <= upperbound:
            return value
        else:
            raise ValueError("invalid bounds for '{}'".format(key))

    def __str__(self):
        return '({:.5f}, {:.5f})'.format(self.latitude, self.longitude)


class Location(Base):
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    city = Column(Text)
    county = Column(Text)
    eco_domain = Column(Text)
    eco_division = Column(Text)
    pop_density = Column(Text)
    terrain = Column(Text)
    land_cover = Column(Text)
    land_owner = Column(Text)
    environment = Column(Text)
    incident_id = Column(Integer, ForeignKey('incidents.id'))
    incident = relationship('Incident', back_populates='location',
                            uselist=False)

    @property
    def region(self):
        if isinstance(self.incident.source, str):
            result = re.search(r'-([A-Z]+)', self.incident.source)
            if result:
                return result.group(1)

    @property
    def country(self):
        if isinstance(self.incident.source, str):
            result = re.search(r'^([A-Z]{1,2})-?', self.incident.source)
            if result:
                return result.group(1)


class Operation(Base):
    __tablename__ = 'operations'

    id = Column(Integer, primary_key=True)
    ipp_type = Column(Text)
    ipp_class = Column(Text)
    ipp_id = Column(Integer, ForeignKey('points.id'))
    ipp = relationship('Point', foreign_keys=[ipp_id],
                       cascade='all, delete-orphan', single_parent=True)
    ipp_accuracy = Column(Float)  # Measured in m
    idot = Column(Float)  # Measured in degrees of true North
    idot_basis = Column(Text)
    dest_id = Column(Integer, ForeignKey('points.id'))
    dest = relationship('Point', foreign_keys=[dest_id],
                        cascade='all, delete-orphan', single_parent=True)
    revised_point_id = Column(Integer, ForeignKey('points.id'))
    revised_point = relationship('Point', foreign_keys=[revised_point_id])
    revision_reason = Column(Text)
    incident_id = Column(Integer, ForeignKey('incidents.id'))
    incident = relationship('Incident', back_populates='operation',
                            uselist=False)

    @validates('ipp_accuracy')
    def validate_sign(self, key, value):
        if value is None or value > 0:
            return value
        else:
            raise ValueError("'{}' must be a positive number".format(key))


class Weather(Base):
    __tablename__ = 'weather'
    MIN_TEMP = -273.15  # Measured in degrees C
    BASE_TEMP = 18  # Measured in degrees C
    WATER_FREEZING_POINT = 0  # Measured in degrees C (approximately)

    id = Column(Integer, primary_key=True)
    high_temp = Column(Float)  # Measured in degrees C
    low_temp = Column(Float)  # Measured in degrees C
    wind_speed = Column(Float)  # Measured in km/h
    rain = Column(Float)  # Measured in mm
    snow = Column(Float)  # Measured in mm
    daylight = Column(Interval)
    solar_radiation = Column(Float)  # Maximum total flux through surface
    description = Column(Text)
    incident_id = Column(Integer, ForeignKey('incidents.id'))
    incident = relationship('Incident', back_populates='weather',
                            uselist=False)

    avg_temp = column_property((high_temp + low_temp)/2)

    @property
    def hdd(self):
        hdd = self.__class__.BASE_TEMP - self.avg_temp
        return hdd if hdd >= 0 else None

    @property
    def cdd(self):
        cdd = self.avg_temp - self.__class__.BASE_TEMP
        return cdd if cdd >= 0 else None

    @validates('high_temp', 'low_temp')
    def validate_bounds(self, key, value):
        lowerbound, upperbound = self.__class__.MIN_TEMP, float('inf')
        if key == 'high_temp' and isinstance(self.low_temp, numbers.Real):
            lowerbound = self.low_temp
        elif isinstance(self.high_temp, numbers.Real):
            upperbound = self.high_temp

        if value is None or lowerbound <= value <= upperbound:
            return value
        else:
            raise ValueError("'high_temp' must be greater than 'low_temp'")

    @validates('wind_speed', 'rain', 'snow', 'solar_radiation')
    def validate_sign(self, key, value):
        if value is None or value >= 0:
            return value
        else:
            raise ValueError("'{}' must be a positive number".format(key))


class Outcome(Base):
    __tablename__ = 'outcomes'

    id = Column(Integer, primary_key=True)
    dec_point_id = Column(Integer, ForeignKey('points.id'))
    dec_point = relationship('Point', foreign_keys=[dec_point_id],
                             cascade='all, delete-orphan', single_parent=True)
    dec_point_type = Column(Text)
    conclusion = Column(Text)
    invest_find = Column(Text)
    find_point_id = Column(Integer, ForeignKey('points.id'))
    find_point = relationship('Point', foreign_keys=[find_point_id],
                              cascade='all, delete-orphan', single_parent=True)
    find_point_accuracy = Column(Float)  # Measured in m
    distance_from_ipp = Column(Float)  # Measured in km
    find_bearing = Column(Float)  # Measured in degrees from true North
    find_feature = Column(Text)
    find_feature_secondary = Column(Text)
    track_offset = Column(Float)  # Measured in m
    elevation_change = Column(Float)  # Measured in m
    incident_id = Column(Integer, ForeignKey('incidents.id'))
    incident = relationship('Incident', back_populates='outcome',
                            uselist=False, cascade='all, delete-orphan',
                            single_parent=True)

    @validates('find_point_accuracy', 'distance_from_ipp', 'find_bearing',
               'track_offset')
    def validate_sign(self, key, value):
        if value is None or value >= 0:
            return value
        else:
            raise ValueError("'{}' must be a positive number".format(key))


class Search(Base):
    __tablename__ = 'searches'

    id = Column(Integer, primary_key=True)
    injured_searcher = Column(Text)
    near_miss = Column(Text)
    find_resource = Column(Text)
    total_tasks = Column(SmallInteger)
    air_tasks = Column(SmallInteger)
    dog_count = Column(SmallInteger)
    air_count = Column(SmallInteger)
    personnel_count = Column(SmallInteger)
    emergent_count = Column(SmallInteger)
    vehicle_count = Column(SmallInteger)
    air_hours = Column(Interval)
    dog_hours = Column(Interval)
    personnel_hours = Column(Interval)
    distance_traveled = Column(Float)  # Measured in km
    lost_equipment = Column(Text)
    total_cost = Column(Float)  # Measured in USD
    incident_id = Column(Integer, ForeignKey('incidents.id'))
    incident = relationship('Incident', back_populates='search', uselist=False)

    @validates('total_tasks', 'air_tasks', 'dog_count', 'air_count',
               'personnel_count', 'emergent_count', 'vehicle_count')
    def validate_sign(self, key, value):
        if value is None or value >= 0:
            return value
        else:
            raise ValueError("'{}' must be a positive number".format(key))


class Incident(Base):
    __tablename__ = 'incidents'

    id = Column(Integer, primary_key=True)
    source = Column(Text)
    key = Column(Text)
    mission = Column(Text)
    number = Column(Text)
    datetime = Column(DateTime)
    location = relationship('Location', back_populates='incident',
                            uselist=False, cascade='all, delete-orphan')
    type = Column(Text)
    disaster_type = Column(Text)
    group = relationship('Group', back_populates='incident', uselist=False,
                         cascade='all, delete-orphan')
    notify_hours = Column(Interval)
    search_hours = Column(Interval)
    total_hours = Column(Interval)
    operation = relationship('Operation', back_populates='incident',
                             uselist=False, cascade='all, delete-orphan')
    weather = relationship('Weather', back_populates='incident', uselist=False,
                           cascade='all, delete-orphan')
    outcome = relationship('Outcome', back_populates='incident', uselist=False,
                           cascade='all, delete-orphan')
    cause = Column(Text)
    search = relationship('Search', back_populates='incident', uselist=False,
                          cascade='all, delete-orphan')
    other = Column(PickleType)  # Dictionary strictly for holding legacy data
    comments = Column(Text)

    lost_hours = column_property(notify_hours + search_hours)
