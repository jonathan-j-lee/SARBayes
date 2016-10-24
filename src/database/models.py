"""
database.models -- Database model definitions

These definitions are based on the 2013 ISRID data standards.
"""

__all__ = ['Subject', 'Group', 'Point', 'Location', 'Operation', 'Outcome',
           'Weather', 'Search', 'Incident']

import numbers
import re

from sqlalchemy import Integer, SmallInteger, Float, Boolean
from sqlalchemy import DateTime, Interval, Text, PickleType, Column, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import and_, not_, select, func, case
from sqlalchemy.orm import column_property, relationship, validates

from database import Base


class Subject(Base):
    """
    An individual from a search-and-rescue incident.

    Attributes:
        __tablename__: The name of the model's SQL table as a string (required
                       by SQLAlchemy).
        SEX_CODES: A dictionary of integer values mapped to string descriptions
                   (see ISO/IEC 5218 for details).
        DOA_TYPES: A list of types of subject status considered equivalent to
                   dead-on-arrival.
    """
    __tablename__ = 'subjects'
    SEX_CODES = {0: 'unknown', 1: 'male', 2: 'female', 9: 'not_applicable'}
    DOA_TYPES = ['DOA', 'Suspended']

    id = Column(Integer, primary_key=True, doc='A unique identifier')
    age = Column(Float, doc='Age at the time of the incident in years')
    sex = Column(SmallInteger, doc='Sex using the encoding standard')
    weight = Column(Float, doc='Weight measured in kg')
    height = Column(Float, doc='Height measured in cm')
    physical_fit = Column(Text, doc="The subject's general physical fitness")
    mental_fit = Column(Text, doc="The subject's general mental fitness")
    personality = Column(Text, doc="The subject's personality")
    experience = Column(Text,
                        doc="The subject's experience at the activity")
    training = Column(Text, doc="The subject's level of survival training")
    equipment = Column(Text, doc="The subject's equipment preparedness "
                                 "(excluding clothing)")
    clothing = Column(Text, doc="The fitness of the subject's clothing for "
                                "the environment")
    status = Column(Text, doc='Status after rescue or location')
    group_id = Column(Integer, ForeignKey('groups.id'), doc='The identifier '
                      'of the group the subject belonged to')
    group = relationship('Group', back_populates='subjects',
                         doc='The group the subject belonged to')

    @hybrid_property
    def sex_as_str(self):
        """ The subject's sex as a human-readable string """
        return self.__class__.SEX_CODES.get(self.sex, None)

    @sex_as_str.expression
    def sex_as_str(cls):
        return case([(cls.sex == code, sex_str)
                     for code, sex_str in cls.SEX_CODES.items()])

    dead_on_arrival = column_property(func.upper(status)
                                      .in_(map(str.upper, DOA_TYPES)),
                                      doc='A boolean indicating whether the '
                                          'subject was dead-on-arrival')
    survived = column_property(not_(func.upper(status)
                                      .in_(map(str.upper, DOA_TYPES))),
                               doc='A boolean indicating whether the subject '
                                   'survived')
    bmi = column_property(weight/height/height*1e4,
                          doc='Body mass index in kg/m^2')

    @validates('age', 'weight', 'height')
    def validate_sign(self, key, value):
        """ Validate the listed attributes are nonnegative. """
        if value is None or value >= 0:  # Possibly rounded down
            return value
        else:
            raise ValueError("'{}' must be a positive number".format(key))

    @validates('sex')
    def validate_sex_code(self, key, value):
        """ Validate that sex conforms to the encoding standard. """
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
    """
    A group in a search-and-rescue incident containing one or more subjects.

    Attributes:
        __tablename__: The name of the model's SQL table as a string.
    """
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True, doc='A unique identifier')
    category = Column(Text, doc='Determined by a hierarchy')
    subcategory = Column(Text, doc='An open text field for further '
                                   'specification')
    activity = Column(Text, doc='The activity the group was performing')
    contact_method = Column(Text, doc='The method by which the SAR agency '
                                      'became aware of the incident')
    scenario = Column(Text, doc='The primary reason the event occurred')
    detectability = Column(Text, doc='How detectable the group was to '
                                     'searchers')
    mobile = Column(Boolean, doc='A boolean indicating if the group was '
                                 'capable of and exhibited movement')
    responsive = Column(Boolean, doc='A boolean indicating if one or more '
                                     'subjects could respond to signals')
    lost_strategy = Column(Text, doc="The group's strategy for being found")
    mobile_hours = Column(Interval, doc='The duration the group was mobile '
                                        'for')
    mechanism = Column(Text, doc='The cause of an injury')
    injury_type = Column(Text, doc='The type of any injuries')
    illness_type = Column(Text, doc='The type of any illnesses')
    treatment = Column(Text, doc='The highest level of treatment a subject '
                                 'receives in the field')
    rescue_method = Column(Text, doc='How the group is evacuated')
    signaling = Column(Text, doc='The signals used by the group to attempt '
                                 'contact with searchers')
    subjects = relationship('Subject', back_populates='group',
                            cascade='all, delete-orphan', doc='The subjects '
                            'belonging to this group')
    incident_id = Column(Integer, ForeignKey('incidents.id'),
                         doc='The identifier of the incident this group was '
                             'involved in')
    incident = relationship('Incident', back_populates='group', uselist=False,
                            doc='The incident this group was involved in')

    size = column_property(select([func.count(Subject.id)])
                           .where(Subject.group_id == id)
                           .correlate_except(Subject),
                           doc='The number of subjects in the group')


class Point(Base):
    """
    A location on the Earth's surface (in three dimensions).

    Attributes:
        __tablename__: The name of the model's SQL table as a string.
        MIN_LATITUDE: The minimum possible latitude in degrees.
        MAX_LATITUDE: The maximum possible latitude in degrees.
        MIN_LONGITUDE: The minimum possible longitude in degrees.
        MAX_LONGITUDE: The maximum possible longitude in degrees.
    """
    __tablename__ = 'points'
    MIN_LATITUDE, MAX_LATITUDE = -90, 90
    MIN_LONGITUDE, MAX_LONGITUDE = -180, 180

    id = Column(Integer, primary_key=True, doc='A unique identifier')
    latitude = Column(Float, doc='Latitude in decimal degrees')
    longitude = Column(Float, doc='Longitude in decimal degrees')
    altitude = Column(Float, doc='Height in m above mean sea level')

    @validates('latitude', 'longitude')
    def validate_bounds(self, key, value):
        """
        Validates latitude and longitude are between their respective bounds.
        """
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
        """ Represent this point as a human-readable coordinate. """
        return '({:.5f}, {:.5f})'.format(self.latitude, self.longitude)


class Location(Base):
    """
    The general location of an incident and a description of the land.

    Attributes:
        __tablename__: The name of the model's SQL table as a string.
    """
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True, doc='A unique identifier')
    name = Column(Text, doc='A name for the general location of the incident')
    city = Column(Text, doc="The city of the incident by the IPP's mailing "
                            "address")
    county = Column(Text, doc='The county of the incident by the IPP')
    eco_domain = Column(Text, doc='The ecoregion domain (Bailey Ecoregions)')
    eco_division = Column(Text, doc='The ecoregion division')
    pop_density = Column(Text, doc='The population density of the area')
    terrain = Column(Text, doc='The topology of the area')
    land_cover = Column(Text, doc='The vegetative cover of the search area')
    land_owner = Column(Text, doc='The land owner type')
    environment = Column(Text, doc='The environment the incident occurred in')
    incident_id = Column(Integer, ForeignKey('incidents.id'),
                         doc='The identifier of the incident that occurred at '
                         'this location')
    incident = relationship('Incident', back_populates='location',
                            uselist=False, doc='The incident that occurred at '
                            'this location')

    @property
    def region(self):
        """
        The region of the country of this location.

        For cases in the United States, the `region` is usually a state.
        """
        if isinstance(self.incident.source, str):
            result = re.search(r'-([A-Z]+)', self.incident.source)
            if result:
                return result.group(1)

    @property
    def country(self):
        """ The country of this location. """
        if isinstance(self.incident.source, str):
            result = re.search(r'^([A-Z]{1,2})-?', self.incident.source)
            if result:
                return result.group(1)


class Operation(Base):
    """
    Information typically known before a search to planners.

    Attributes:
        __tablename__: The name of the model's SQL table as a string.
    """
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
    """
    Attributes:
        __tablename__: The name of the model's SQL table as a string.
    """
    __tablename__ = 'weather'
    MIN_TEMP = -273.15  # Measured in degrees C (for sanity checks)
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
    """
    Attributes:
        __tablename__: The name of the model's SQL table as a string.
    """
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
    """
    Attributes:
        __tablename__: The name of the model's SQL table as a string.
    """
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
    """
    Attributes:
        __tablename__: The name of the model's SQL table as a string.
    """
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
