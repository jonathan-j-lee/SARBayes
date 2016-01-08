"""
database.models
"""

__all__ = 'Subject', 'Group', 'Incident'

from sqlalchemy import Column
from sqlalchemy import Integer, SmallInteger, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import validates, relationship

from . import Base


class Subject(Base):
    """
    A lost person involved in a search-and-rescue incident.
    """
    __tablename__ = 'subjects'
    # See ISO/IEC 5218
    sexes = {0: 'unknown', 1: 'male', 2: 'female', 9: 'not applicable'}

    identifier = Column(Integer, primary_key=True)
    sex = Column(SmallInteger)
    age = Column(Float)  # Measured in years
    weight = Column(Float)  # Measured in kg
    height = Column(Float)  # Measured in cm
    physical_fitness = Column(Text)
    mental_fitness = Column(Text)
    personality = Column(Text)
    experience = Column(Text)
    training = Column(Text)
    equipment = Column(Text)
    clothing = Column(Text)
    group_identifier = Column(Integer, ForeignKey('groups.identifier'))
    group = relationship('Group', back_populates='subjects')

    @validates('sex', 'age', 'weight', 'height')
    def validate(self, key: str, value: object) -> (object):
        """
        Validate certain attributes of this model upon assignment.
        Raises `ValueError`.
        """
        if key == 'sex':
            if value not in self.__class__.sexes:
                raise ValueError("invalid code for '{}'".format(key))

        if key in ('age', 'weight', 'height'):
            value = float(value)  # Coerce other numberic types to a float
            if value <= 0.0:
                raise ValueError("'{}' is not a positive number".format(key))

        return value

    @property
    def bmi(self) -> (float):
        """
        Calculate the subject's body mass index (BMI) on-the-fly.
        This attribute is measured in kg/cm^2.
        """
        if self.weight is not None and self.height is not None:
            return self.weight/pow(self.height, 2)


class Group(Base):
    """
    A collection of one or more subjects involved in the same incident.
    """
    __tablename__ = 'groups'

    identifier = Column(Integer, primary_key=True)
    category = Column(Text)
    subcategory = Column(Text)
    activity = Column(Text)
    contact_method = Column(Text)
    subjects = relationship('Subject', back_populates='group')
    incident_identifier = Column(Integer, ForeignKey('incidents.identifier'))
    incident = relationship('Incident', back_populates='group', uselist=False)


class Incident(Base):
    """
    A search-and-rescue incident.
    """
    __tablename__ = 'incidents'

    identifier = Column(Integer, primary_key=True)
    group = relationship('Group', back_populates='incident', uselist=False)
