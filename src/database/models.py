"""
database.models
"""

__all__ = ['Subject', 'Group', 'Point', 'Location', 'Weather', 'Incident']

import re

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
    scenario = Column(Enum('avalanche', 'criminal', 'despondent', 'disaster',
                           'evading', 'investigative', 'lost', 'medical',
                           'drowning', 'overdue', 'stranded', 'trauma',
                           name='scenario_types'))
    detectability = Column(Enum('excellent', 'good', 'fair', 'poor',
                                name='detectability_types'))
    mobile = Column(Boolean)
    responsive = Column(Boolean)
    lost_strategy = Column(Enum('back_tracking', 'contouring',
                                'direction_sampling', 'direction_travelling',
                                'downhill', 'evasive', 'folk_wisdom',
                                'followed_travel_aid', 'landmark', 'panicked',
                                'nothing', 'route_sampling', 'stayed_put',
                                'view_enhancing', 'other',
                                name='lost_strategy_types'))
    lost_strategy_details = Column(Text)
    mobile_hours = Column(Interval)
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

    @property
    def region(self):
        try:
            result = re.search('-([A-Z]+)', self.incident.source)
            return result.group(1)
        except AttributeError:
            return None

    @property
    def country(self):
        try:
            result = re.search(r'^([A-Z]{1,2})-', self.incident.source)
            return result.group(1)
        except AttributeError:
            return None


class Operation(Base):
    __tablename__ = 'operations'
    id = Column(Integer, primary_key=True)
    ipp_type = Column(Enum('airport', 'beacon', 'building', 'field',
                           'radar_contact', 'residence', 'road', 'signal',
                           'trail', 'trailhead', 'vehicle', 'water',
                           'forested_area', 'perennial_ice', 'rock', 'shrub',
                           'wetland', name='ipp_type_types'))
    ipp_class = Column(Enum('pls', 'lkp', name='ipp_class_types'))
    ipp_id = Column(Integer, ForeignKey('points.id'))
    ipp = relationship('Point', foreign_keys=[ipp_id])
    ipp_accuracy = Column(Enum('1000', '100', '10', '1',
                               name='ipp_accuracy_types'))  # Measured in m
    idot = Column(Enum('intended_destination', 'circuit', 'physical_clue',
                       'sighting', 'tracks', 'radar_tracks', 'tracking_dogs',
                       'other', name='idot_types'))
    idot_details = Column(Text)
    dest_id = Column(Integer, ForeignKey('points.id'))
    dest = relationship('Point', foreign_keys=[dest_id])
    revised_point_id = Column(Integer, ForeignKey('points.id'))
    revised_point = relationship('Point', foreign_keys=[revised_point_id])
    revision_reason = Column(Text)
    incident_id = Column(Integer, ForeignKey('incidents.id'))
    incident = relationship('Incident', back_populates='operation',
                            uselist=False)


class Outcome(Base):
    __tablename__ = 'outcomes'
    id = Column(Integer, primary_key=True)
    dec_point_id = Column(Integer, ForeignKey('points.id'))
    dec_point = relationship('Point', foreign_keys=[dec_point_id])
    dec_point_type = Column(Enum('saddle', 'shortcut', 'trail_animal',
                                 'trail_junction', 'trail_social',
                                 'trail_turnoff', 'other',
                                 name='dec_point_type_types'))
    dec_point_type_details = Column(Text)
    conclusion = Column(Enum('open', 'closed', 'suspended',
                             'closed_post_suspension',
                             name='conclusion_types'))
    invest_find = Column(Boolean)
    invest_find_reason = Column(Enum('took_transportation', 'with_friend',
                                     'with_family', 'bastard_case', 'in_jail',
                                     'in_hospital', 'in_shelter', 'runaway',
                                     'staged', 'other',
                                     name='invest_find_reason_types'))
    invest_find_details = Column(Text)
    find_point_id = Column(Integer, ForeignKey('points.id'))
    find_point = relationship('Point', foreign_keys=[find_point_id])
    # Measured in m
    find_point_accuracy = Column(Enum('1000', '100', '10', '1',
                                      name='find_point_accuracy_types'))
    dist_from_ipp = Column(Float)  # Measured in km
    find_bearing = Column(Float)  # Measured in degrees from true North
    find_feature = Column(Enum('aiport', 'building', 'field', 'structure',
                               'road', 'trail', 'trailhead', 'vehicle',
                               'water', 'forested_area', 'perennial_ice',
                               'rock', 'shrub', 'wetland',
                               name='find_feature_types'))
    find_feature_details = Column(Text)
    track_offset = Column(Float)  # Measured in m
    elevation_change = Column(Float)  # Measured in m
    incident_id = Column(Integer, ForeignKey('incidents.id'))
    incident = relationship('Incident', back_populates='outcome',
                            uselist=False)


class Weather(Base):
    __tablename__ = 'weather'
    base_temp = 18  # Measured in degrees C
    id = Column(Integer, primary_key=True)
    high_temp = Column(Float)
    low_temp = Column(Float)
    wind_speed = Column(Float)  # Measured in km/h
    rain = Column(Float)  # Measured in mm
    snow = Column(Float)  # Measured in mm
    daylight = Column(Interval)
    description = Column(Text)
    incident_id = Column(Integer, ForeignKey('incidents.id'))
    incident = relationship('Incident', back_populates='weather',
                            uselist=False)

    @property
    def avg_temp(self):
        return (self.high_temp + self.low_temp)/2

    @property
    def hdd(self):
        hdd_ = self.__class__.base_temp - avg_temp
        return hdd_ if hdd_ > 0 else None

    @property
    def cdd(self):
        cdd_ = avg_temp - self.__class__.base_temp
        return cdd_ if cdd_ > 0 else None


class Incident(Base):
    __tablename__ = 'incidents'
    id = Column(Integer, primary_key=True)
    source = Column(Enum('AU', 'CA-BC', 'CA-HC', 'CA-NB', 'CA-NS', 'CA-ON',
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
    disaster_related = Column(Boolean)
    disaster_type = Column(Enum('cbrne', 'dam', 'earthquake', 'fire',
                                'flooding', 'hurricane', 'landslide',
                                'tornado', 'tsunami', 'volcano',
                                'winter_storm', 'other',
                                name='disaster_type_types'))
    disaster_type_details = Column(Text)
    group = relationship('Group', back_populates='incident', uselist=False)
    notify_hours = Column(Interval)
    search_hours = Column(Interval)
    total_hours = Column(Interval)
    operation = relationship('Operation', back_populates='incident',
                             uselist=False)
    weather = relationship('Weather', back_populates='incident', uselist=False)
    outcome = relationship('Outcome', back_populates='incident', uselist=False)
    cause = Column(Enum('avalanche', 'darkness', 'decision_point',
                        'despondent', 'drowning', 'environment', 'fitness',
                        'medical', 'overdue', 'poor_supervision',
                        'poor_trails', 'poor_equipment', 'poor_map', 'runaway',
                        'accidental_separation', 'intentional_separation',
                        'shortcut', 'intoxication', 'trauma', 'violence',
                        'wandered_away', name='cause_types'))

    @property
    def lost_hours(self):
        return self.notify_hours + self.search_hours
