"""
database
========
"""

__all__ = ['Base', 'cleaning', 'models', 'initialize', 'processing',
           'terminate']

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from . import cleaning, models, processing


def __bool__(self):
    for column in self.__mapper__.columns:
        if not column.primary_key:
            if getattr(self, column.name) != None:
                return True

    return False


def __getitem__(self, name):
    return self.__mapper__.columns[name]


def __repr__(self):
    return '{}(id={})'.format(self.__class__.__name__, self.id)


Base.__bool__ = __bool__
Base.__getitem__ = __getitem__
Base.__repr__ = Base.__str__ = __repr__


def initialize(url):
    engine = create_engine(url, convert_unicode=True)
    session = scoped_session(sessionmaker(bind=engine))
    Base.query = session.query_property()
    Base.metadata.create_all(bind=engine)
    return engine, session


def terminate(engine, session):
    session.close_all()
    engine.dispose()
