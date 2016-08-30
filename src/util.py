"""
util -- Utilities for configuration and logging
"""

import logging
import sys
import yaml

import database
from database.models import Subject, Group, Incident
from database.processing import tabulate
import weather


def configure_api_access(filename):
    with open(filename) as config_file:
        config = yaml.load(config_file.read())

    weather.wsi.DEFAULT_PARAMETERS['userKey'] = config['wsi']['key']
    weather.noaa.API_TOKEN = config['noaa']['key']


def initialize_logging(filename, mode='a+', logger=None):
    if logger is None:
        logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(levelname)s][%(asctime)s] > %(message)s')

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(filename, mode)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.debug('Logging initialized')


def read_simple_data(url, exclude_singles=False, exclude_groups=False):
    engine, session = database.initialize(url)

    columns = Incident.total_hours, Subject.survived, Group.category
    query = session.query(*columns).join(Group, Subject)
    if exclude_singles:
        query = query.filter(Group.size > 1)
    if exclude_groups:
        query = query.filter(Group.size == 1)

    database.terminate(engine, session)

    df = tabulate(query)
    df = df.assign(days=[total_hours.total_seconds()/3600/24
                         for total_hours in df.total_hours],
                   doa=[not survived for survived in df.survived])
    df = df[0 <= df.days]

    return df
