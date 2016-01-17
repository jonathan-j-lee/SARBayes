"""
database.models
"""

__all__ = ['Subject']

from sqlalchemy import (Column, Integer, SmallInteger, Float, Interval,
                        DateTime, Boolean, Text, Enum, ForeignKey)
from sqlalchemy.orm import relationship, validates

from . import Base


class Subject(Base):
    __tablename__ = 'subjects'
    id = Column(Integer, primary_key=True)
    age = Column(Float)  # Measured in years
    sex = Column(Enum('male', 'female', name='sex_types'))
    weight = Column(Float)  # Measured in kg
    height = Column(Float)  # Measured in cm
    physical_fit = Column(Enum('excellent', 'good', 'fair', 'poor',
                               name='physical_fit_types'))
    mental_fit = Column(Enum('excellent', 'good', 'fair', 'poor',
                             name='mental_fit_types'))
    personality = Column(Enum('confident', 'outgoing', 'unsure', 'withdrawn',
                              'suicidal', name='personality_types'))
    experience = Column(Enum('excellent', 'good', 'fair', 'poor',
                             name='experience_types'))
    training = Column(Enum('excellent', 'good', 'fair', 'poor',
                           name='training_types'))
    equipment = Column(Enum('excellent', 'good', 'fair', 'poor',
                            name='equipment_types'))
    clothing = Column(Enum('excellent', 'good', 'fair', 'poor',
                           name='clothing_types'))
    group_id = Column(Integer, ForeignKey('groups.id'))
    group = relationship('Group', back_populates='subjects')

    @property
    def bmi(self):
        return self.weight/pow(self.height, 2)


class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    category = Column(Enum('water', 'fire', 'earthquake', 'landslide',
                           'volcano', 'tornado', 'cbrne', 'abduction',
                           'aircraft', 'vehicle', 'four_wheeled_drive_vehicle',
                           'atv', 'motorcycle', 'mountain_bicycle',
                           'tracked_vehicle', 'dementia', 'despondent', 'asd',
                           'mental_illness', 'intellectual_disability',
                           'child', 'hiker', 'hunter', 'angler', 'car_camper',
                           'caver', 'climber', 'gatherer', 'horseback_rider',
                           'base_jumper', 'extreme_sports', 'runner',
                           'skier_alpine', 'skier_nordic', 'snowboarder',
                           'snowshoer', 'substance_intoxication', 'worker',
                           'other', name='category_names'))
    subcategory = Column(Text)
    activity = Column(Text)
    contact_method = Column(Enum('reported_missing', 'vehicle_found',
                                 'registration', '406_beacon', 'elt',
                                 'send_beacon', 'pers', 'cell_phone', 'radio',
                                 'distress_signal',
                                 name='contact_method_types'))
    subjects = relationship('Subject', back_populates='group')
    incident_id = Column(Integer, ForeignKey('incidents.id'))
    incident = relationship('Incident', back_populates='group', uselist=False)

    @property
    def size(self):
        return len(self.subjects)


class Point(Base):
    __tablename__ = 'points'
    id = Column(Integer, primary_key=True)
    latitude = Column(Float)  # Measured in decimal degrees
    longitude = Column(Float)  # Measured in decimal degrees
    altitude = Column(Float)  # Measured in m


class Location(Base):
    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    city = Column(Text)
    county = Column(Text)
    region = Column(Text)
    country = Column(Text)
    eco_domain = Column(Enum('polar', 'temperate', 'dry', 'tropical',
                             name='eco_domain_types'))
    eco_division = Column(Enum('110', 'M110', '120', 'M120', '130',
                               'M130', '210', 'M210', '220', 'M220',
                               '230', 'M230', '240', 'M240', '250',
                               'M250', '260', 'M260', '310', 'M310',
                               '320', 'M320', '330', 'M330', '340',
                               'M340', '410', 'M410', '420', 'M420', 'M',
                               name='eco_division_types'))
    pop_density = Column(Enum('wilderness', 'rural', 'suburban', 'urban',
                              'water', name='pop_density_types'))
    terrain = Column(Enum('mountainous', 'hilly', 'flat', 'water',
                          name='terrain_types'))
    land_cover = Column(Enum('bare', 'light', 'moderate', 'heavy', 'water',
                             name='land_cover_types'))
    land_owner = Column(Enum('private', 'commercial', 'county', 'state', 'nps',
                             'usfs', 'blm', 'military', 'native', 'navigable',
                             'other', name='land_owner_types'))
    land_owner_details = Column(Text)
    environment = Column(Enum('land', 'air', 'water', 'cave',
                              name='environment_types'))
    incident_id = Column(Integer, ForeignKey('incidents.id'))
    incident = relationship('Incident', back_populates='location',
                            uselist=False)


class Incident(Base):
    __tablename__ = 'incidents'
    id = Column(Integer, primary_key=True)
    source = Column(Enum('AU', 'CA-BC', 'CA-HC', 'CA-NB', 'CA-NS', 'CA-Qn',
                         'CA-QU', 'CH', 'ES', 'IS', 'I-SRG', 'I-GEOS', 'NZ',
                         'PL', 'SA', 'UK', 'UK-P', 'US-AF', 'US-AFK',
                         'US-NOAA', 'US-NPS', 'US-NPSyo', 'US-FEMA', 'US-AK',
                         'US-AZ', 'US-BM', 'US-CA', 'US-CAc', 'US-CAm',
                         'US-CAs', 'US-CO', 'US-GA', 'US-ID', 'US-IN', 'US-KY',
                         'US-MA', 'US-MD', 'US-ME', 'US-MEa', 'US-NH', 'US-NM',
                         'US-NJ', 'US-NY', 'US-OR', 'US-PA', 'US-PL', 'US-UT',
                         'US-VT', 'US-VA', 'US-WA', 'US-WI', 'US-WY',
                         name='source_types'))
    key = Column(Text)
    mission = Column(Text)
    number = Column(Text)
    datetime = Column(DateTime)
    location = relationship('Location', back_populates='incident',
                            uselist=False)
    type = Column(Enum('search', 'rescue', 'water', 'training', 'beacon',
                       'recovery', 'aircraft', 'false_report', 'standby',
                       'assist', 'attempt_to_locate', 'evidence',
                       name='type_types'))
    disaster_type = Column(Enum('cbrne', 'dam', 'earthquake', 'fire',
                                'flooding', 'hurricane', 'landslide',
                                'tornado', 'tsunami', 'volcano',
                                'winter_storm', 'none', 'other',
                                name='disaster_type_types'))
    disaster_type_details = Column(Text)
    group = relationship('Group', back_populates='incident', uselist=False)
