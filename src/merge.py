#!/usr/bin/env python3

"""
merge -- A standalone extensible script for adding data to the database backend

This script contains rules for importing data in a variety of sources
(currently, this mainly encompasses Excel spreadsheets) into a single
SQLAlchemy environment.

Sample usage:

>>> @Registry.add('my-workbook.xlsx', 'my-worksheet')
>>> def procedure(index, labeled_row, mapping):
>>>     ...  # Your code here

Glossary:
  - A labeled row is a dictionary where each raw column name maps to a value
    (in essence, column names are used instead of indices to represent rows).
  - A mapping is a dictionary where each raw column name points to the
    attribute of a model instance.
  - Every procedure is a function that accepts an index, labeled row, and
    mapping, and yields an iterable of database models. These acts as rules for
    how to add a particular worksheet to the backend.

Notes:
  - The name of the procedure does not matter.
  - You may access the logger as `logging.getLogger()`.
  - If a straightforward one-to-one conversion is available, you may add it
    to the mappings file (`SARBayes/data/mappings.yaml`) like so:

        my-workbook:
            my-worksheet:
                my-excel-heading:   my-model-attribute

    Then, call `setup_models`, which will call `automap` and seek out the type
    of the attribute and attempt type coercion if the raw value does not have
    the same type as the model attribute.
  - Once the data are added, disable the procedure when running the script in
    the future by adding `enabled=False` to the decorator.
"""

import datetime
import logging
import openpyxl
import os
import warnings
import yaml

import database
from database.cleaning import extract_numbers, coerce_type
from database.models import Subject, Group, Point, Location, Weather
from database.models import Operation, Outcome, Search, Incident
from util import initialize_logging

EXCEL_START_DATE = datetime.datetime(1900, 1, 1)


def read_excel(filename):
    """
    Read each worksheet from an Excel workbook file.

    Arguments:
        filename: A string representing the path to the file.

    Returns:
        A generator containing worksheet title-and-row generator pairs. The
        title is a string representing the worksheet's title. The row generator
        is another inner generator that iterates over the worksheet's rows,
        each of which is represented as a tuple of values.
    """
    workbook = openpyxl.load_workbook(filename, read_only=True)
    for worksheet in workbook:
        rows = (tuple(cell.value for cell in row) for row in worksheet.rows)
        yield worksheet.title, rows


class Registry:
    """
    A global namespace for holding procedures.

    Attributes:
        instances: A dictionary mapping keys to procedures.
        serialize: A callable that converts a sequence of labels into a
                   hashable key (by default, serialization is implemented as
                   the immutable set's constructor).
    """
    instances, serialize = {}, frozenset

    @classmethod
    def add(cls, *labels, enabled=True):
        """
        A decorator for adding a procedure to the registry.

        Arguments:
            cls: The `Registry` class object.
            labels: A variable number of values to attach to the procedure.
            enabled: A boolean indicating whether or not to exclude the
                     procedure (used when the procedure has already been used
                     on a worksheet, and should not be used in future script
                     runs).

        Returns:
            A one-argument wrapper function that takes another function, adds
            it to the registry, and returns it (the behavior of the wrapper and
            original functions are identical).
        """
        def wrapper(function):
            if enabled:
                cls.instances[cls.serialize(labels)] = function
            return function

        return wrapper

    @classmethod
    def retrieve(cls, *labels):
        """
        A class method for retrieving a procedure from the registry.

        Arguments:
            cls: The `Registry` class object.
            labels: A variable number of values attached to the procedure.

        Returns:
            The procedure (that is, a function) if the labels are found in the
            registry, or `None` otherwise.
        """
        return cls.instances.get(cls.serialize(labels), None)


def automap(index, labeled_row, mapping, **models):
    """
    Map each row's raw values to the corresponding column in the database
    models, attempting type conversion when possible.

    Arguments:
        index: The index of `labeled_row` in the current table or worksheet.
        labeled_row: A dictionary mapping each raw column name to the row's
                     corresponding value (see module docstring for definition).
        mapping: A dictionary mapping raw column names to model attributes.
        models: A variable number of keyword arguments mapping names to model
                instances.
    """
    logger = logging.getLogger()

    for old, new in mapping.items():
        try:
            name, attribute = new.split('.')
            model = models[name]
            datatype = model[attribute].type.python_type
            coerced_value = coerce_type(labeled_row[old], datatype)

            if coerced_value is not None:
                setattr(model, attribute, coerced_value)
                del labeled_row[old]

        except ValueError as error:
            message = 'Instance {} ({}): {}'
            logger.warning(message.format(index + 1, new, error))


def setup_models(index, labeled_row, mapping):
    """
    Initialize a new set of instances and fill in their attributes naively.

    Arguments:
        index: The index of `labeled_row` in the current table or worksheet.
        labeled_row: A dictionary mapping each raw column name to the row's
                     corresponding value (see module docstring for definition).
        mapping: A dictionary mapping raw column names to model attributes.

    Returns:
        Instances of the `Group`, `Location`, `Weather`, `Operation`,
        `Outcome`, `Search`, and `Incident` models, in that order.
    """
    group, location, weather = Group(), Location(), Weather()
    operation, outcome, search = Operation(), Outcome(), Search()
    incident = Incident(group=group, location=location, weather=weather,
                        operation=operation, outcome=outcome,
                        search=search)

    automap(index, labeled_row, mapping, group=group, location=location,
            weather=weather, operation=operation, outcome=outcome,
            search=search, incident=incident)

    return group, location, weather, operation, outcome, search, incident


@Registry.add('ISRIDclean.xlsx', 'ISRIDclean', enabled=False)
def procedure(index, labeled_row, mapping):
    """ A procedure for the `ISRIDclean` worksheet. """

    logger = logging.getLogger()
    models = setup_models(index, labeled_row, mapping)
    group, location, weather, operation, outcome, search, incident = models

    physical_fit = coerce_type(labeled_row['Physical Fitness'], str)
    mental_fit = coerce_type(labeled_row['Mental Fitness'], str)
    experience = coerce_type(labeled_row['Experience'], str)
    equipment = coerce_type(labeled_row['Equipment'], str)
    personality = coerce_type(labeled_row['Personality'], str)
    clothing = coerce_type(labeled_row['Clothing'], str)
    training = coerce_type(labeled_row['Survival training'], str)

    ages = str(labeled_row['Age'] or '').strip().replace('.', ',')
    ages = [float(age.replace('0s', '5')) if age != '?' else None
            for age in ages.split(',') if age]

    sexes = str(labeled_row['Sex'] or '').strip().upper()
    translation = {'M': 'male', 'F': 'female', '?': None}
    sexes = [translation[sex] for sex in sexes if sex in translation]

    statuses = str(labeled_row['Subject Status'] or '').strip().upper()
    statuses = list(filter(lambda status: status, statuses.split(',')))

    number_lost = coerce_type(labeled_row['Number Lost'], int)
    number_lost = max(number_lost or 0, len(ages), len(sexes), len(statuses))

    if number_lost > 0:
        def fill(sequence):
            if len(sequence) == 0:
                return [None]*number_lost
            elif len(sequence) == 1:
                return sequence*number_lost
            else:
                return sequence

        ages, sexes, statuses = fill(ages), fill(sexes), fill(statuses)

        if not (number_lost == len(ages) == len(sexes) == len(statuses)):
            message = 'Instance {}: subject count ({}), anomaly detected'
            logger.warning(message.format(index + 1, number_lost))

        else:
            for index in range(number_lost):
                subject = Subject(age=ages[index], sex=sexes[index],
                                  physical_fit=physical_fit,
                                  mental_fit=mental_fit,
                                  personality=personality,
                                  experience=experience,
                                  training=training, equipment=equipment,
                                  clothing=clothing, status=statuses[index],
                                  group=group)

                if number_lost == 1:
                    subject.weight = coerce_type(labeled_row['Weight (Kg)'],
                                                 float)
                    subject.height = coerce_type(labeled_row['Height (Cm)'],
                                                 float)

                yield subject

    responsive_text = coerce_type(labeled_row['Responsivenss'], str)
    if isinstance(responsive_text, str):
        responsive_text = responsive_text.strip().casefold()
        group.responsive = responsive_text == 'responsive'.casefold()
        del labeled_row['Responsivenss']

    mobile_text = coerce_type(labeled_row['Mobility'], str)
    if isinstance(mobile_text, str):
        mobile_text = mobile_text.strip().casefold()
        group.mobile = mobile_text == 'mobile'.casefold()
        del labeled_row['Mobility']

    elevation_change = labeled_row['Elevation Change (ft)']
    outcome.elevation_change = coerce_type(elevation_change, float)
    if isinstance(outcome.elevation_change, float):
        outcome.elevation_change *= 0.3048
        del labeled_row['Elevation Change (ft)']

    del labeled_row['Distance IPP (miles)']
    del labeled_row['Distance Invest. (miles)']

    incident.other = {attribute: value for attribute, value in
                      labeled_row.items() if value is not None}

    yield from models


@Registry.add('ISRIDnew-data-20150721.xlsx', enabled=False)
@Registry.add('ISRID 2015 NY cleaned and corrected data '
              '991 cases through 2014-01-06.xlsx', 'SDF', enabled=False)
@Registry.add('combined NPS Data (SEKI and ZION).xlsx', 'SDF', enabled=False)
def procedure(index, labeled_row, mapping):
    """ A procedure for merging worksheet in standard data format (SDF). """

    if 'Medical Type' in labeled_row:
        labeled_row['Illness Type'] = None

    logger = logging.getLogger()
    models = setup_models(index, labeled_row, mapping)
    group, location, weather, operation, outcome, search, incident = models

    disaster_related = labeled_row.pop('Disaster Related')
    if disaster_related is not None:
        if disaster_related.strip().casefold() == 'no'.casefold():
            incident.disaster_type = 'none'
        elif incident.disaster_type is None:
            incident.disaster_type = 'unspecified disaster'

    state = labeled_row.pop('Mobility Responsiveness')
    if state is not None:
        state = state.strip().lower()
        if state:
            group.mobile = 'immobile' not in state
            group.responsive = 'unresponsive' not in state

    elevation_change = labeled_row['Elevation Change (ft)']
    outcome.elevation_change = coerce_type(elevation_change, float)
    if isinstance(outcome.elevation_change, float):
        outcome.elevation_change *= 0.3048
        del labeled_row['Elevation Change (ft)']

    subject_mapping = {
        'Age': 'age',
        'Sex': 'sex',
        'Weight (Kg)': 'weight',
        'Height (Cm)': 'height',
        'Physical Fitness': 'physical_fit',
        'Mental Fitness': 'mental_fit',
        'Experience': 'experience',
        'Equipment': 'equipment',
        'Clothing': 'clothing',
        'Survival training': 'training',
        'Personality': 'personality',
        'Subject Status': 'status'
    }

    for number in range(1, 6):
        suffix, subject, empty = str(number).replace('1', ''), Subject(), True
        for old, new in subject_mapping.items():
            old += suffix
            datatype = subject[new].type.python_type
            if new == 'sex':
                datatype = str

            try:
                value = coerce_type(labeled_row[old], datatype)
            except ValueError as error:
                message = 'Instance {} ({}): {}'
                logger.warning(message.format(index + 1,
                                              'subject.' + new, error))
                continue

            if new == 'sex' and isinstance(value, str):
                value = value.strip().lower()
                if 'm' in value:
                    value = 'male'
                elif 'f' in value:
                    value = 'female'
                else:
                    if value not in ('', 'unknown'):
                        message = ('Instance {} (subject.sex):'
                                  ' "{}" invalid code')
                        logger.warning(message.format(index + 1, value))
                    value = None

            setattr(subject, new, value)

            if getattr(subject, new) is not None:
                del labeled_row[old]
                empty = False

        if not empty:
            subject.group = group
            yield subject

    point_mapping = {
        'IPP Coord. ': 'operation.ipp',
        'Destination Coord.': 'operation.dest',
        'Revised LKP/PLS (N/S)': 'operation.revised_point',
        'Decision Point coord': 'outcome.dec_point',
        'Find Coord': 'outcome.find_point'
    }

    for old, new in point_mapping.items():
        try:
            value = coerce_type(labeled_row[old], str)
            if value is None or value.strip().lower() in ('', 'unknown'):
                del labeled_row[old]
                continue

            latitude, longitude = tuple(map(float, value.split(',')))
            point = Point(latitude=latitude, longitude=longitude)

            model, (*references, attribute) = incident, new.split('.')
            for reference in references:
                model = getattr(model, reference)

            setattr(model, attribute, point)
            yield point
            del labeled_row[old]

        except (TypeError, ValueError) as error:
            message = 'Instance {} ({}): "{}" are invalid coordinates'
            logger.warning(message.format(index + 1, new, value))

    del labeled_row['Distance IPP (miles)']
    del labeled_row['Distance Invest. (miles)']

    incident.other = {attribute: value for attribute, value in
                      labeled_row.items() if value is not None}

    yield from models


def execute():
    """
    Import and merge new data into the backend.

    Currently only handles Excel spreadsheets, but can be extended to other
    data sources.
    """
    warnings.filterwarnings('ignore')
    initialize_logging('../logs/merge.log', 'a+')

    logger = logging.getLogger()
    engine, session = database.initialize('sqlite:///../data/isrid-master.db')

    with open('../data/mappings.yaml') as mappings_file:
        mappings = yaml.load(mappings_file.read())

    for filename in os.listdir('../data/'):
        if filename.endswith('.xlsx'):
            for title, rows in read_excel(os.path.join('../data/', filename)):
                procedure = Registry.retrieve(filename, title)
                procedure = procedure or Registry.retrieve(filename)
                mapping = mappings.get(filename, {}).get(title, {})

                if procedure:
                    message = "Merging '{}' from '{}' ... "
                    logger.info(message.format(title, filename))
                    labels = list(next(rows))

                    if labels.count('Equipment4') > 1:
                        index = labels[::-1].index('Equipment4')
                        labels[-index - 1] = 'Equipment5'

                    for index, row in enumerate(rows):
                        labeled_row = dict(zip(labels, row))
                        for model in procedure(index, labeled_row, mapping):
                            session.add(model)

                    session.commit()

    logging.shutdown()
    database.terminate(engine, session)


if __name__ == '__main__':
    execute()
