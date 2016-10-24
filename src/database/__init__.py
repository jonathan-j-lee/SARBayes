"""
database -- ISRID SQLAlchemy backend

The purpose of this database backend is to provide a single high-level
interface between the data collected in a variety of files for ISRID and a
model developer. SQL comes with several advantages over Excel, most notably
easier subsetting and strict typing.
"""

__all__ = ['Base', 'cleaning', 'models', 'initialize', 'processing',
           'terminate']

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from . import cleaning, models, processing


def __bool__(self):
    """
    Determine whether or not the instance contains any data (is nonempty).

    Returns:
        `False` if all the attributes of `self` are empty, or `True` otherwise.

    This method does not inspect related instances (that is, this is a shallow
    inspection).
    """
    for column in self.__mapper__.columns:
        if not column.primary_key:
            if ('anon' not in column.name and
                    getattr(self, column.name) != None):
                return True
    return False


def __getitem__(self, name):
    """
    Look up a SQLAlchemy column by name.

    Arguments:
        name: A string representing the name of a column.

    Returns:
        A SQLAlchemy `Column` object with the given `name`, or `None` if no
        column has the name.
    """
    return self.__mapper__.columns.get(name, None)


def __repr__(self):
    """
    Provide a machine-readable representation of `self`.

    Returns:
        A string that, when evaluated, should produce a model instance
        equivalent to `self`.
    """
    attributes = ((attribute, getattr(self, attribute))
                  for attribute in self.__class__.__mapper__.columns.keys())
    pairs = ('{}={}'.format(attribute, repr(value))
             for attribute, value in attributes if value is not None)
    return '{}({})'.format(self.__class__.__name__, ', '.join(pairs))


# Assign magic methods to `Base` parent class
Base.__bool__ = __bool__
Base.__getitem__ = __getitem__
Base.__repr__ = Base.__str__ = __repr__


def initialize(url):
    """
    Initialize a connection to the database.

    Arguments:
        url: A string representing a URL to the database.

    Returns:
        engine: A SQLAlchemy engine object.
        session: A SQLAlchemy scoped session object.
    """
    engine = create_engine(url, convert_unicode=True)
    session = scoped_session(sessionmaker(bind=engine))
    Base.query = session.query_property()
    Base.metadata.create_all(bind=engine)
    return engine, session


def terminate(engine, session):
    """
    Terminate a connection to the database (cleanly).

    Arguments:
        engine: A SQLAlchemy engine object obtained from `initialize`.
        session: A SQLAlchemy scoped session object obtained from `initialize`.
    """
    session.close_all()
    engine.dispose()
