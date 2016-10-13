"""
util -- Shared utilities for configuration and logging
"""

import logging
import sys
import yaml

import database
from database.models import Subject, Group, Incident
from database.processing import tabulate
import weather


def configure_api_access(filename='../data/config.yaml'):
    """
    Read API keys from a YAML configuration file and store them module-wide.

    For accessing the weather APIs, the file should have the form:

        wsi:
            key: <your key here>
        noaa:
            key: <your key here>

    Arguments:
        filename: A string representing the path to the configuration file. By
                  default, this path is `../data/config.yaml`.
    """
    with open(filename) as config_file:
        config = yaml.load(config_file.read())

    weather.wsi.DEFAULT_PARAMETERS['userKey'] = config['wsi']['key']
    weather.noaa.API_TOKEN = config['noaa']['key']


def initialize_logging(filename, mode='a+', logger=None):
    """
    Initialize a logger to stream to both a file and standard output.

    Arguments:
        filename: A string representing the path to a log file. If no such file
                  exists, the logger will try to create one.
        mode: A string representing the behavior of the log file. By default,
              new data is appended to the file.
        logger: A logger object. If no logger object is provided (that is, the
                default argument `None` is passed in), use a nameless logger.
    """
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
    """
    Read incident duration, survival, and category data. A useful shorthand.

    Arguments:
        url: A string representing the database URL to connect to.
        exclude_singles: A boolean indicating whether the query should exclude
            subjects from groups with exactly one member.
        exclude_groups: A boolean indicating whether the query should exclude
            subjects from groups with more than one members.

    Returns:
        A pandas dataframe containing the lost person data. The columns include
        `total_hours`, `survived`, `category`, `days` (the incident duration in
        days, as taken from `total_hours`), and `doa` (a boolean that is `True`
        is the subject did not survive). Cases with a negative timedelta
        `Incident.total_hours` are filtered out.

    Warning:
        If `exclude_singles` is `True` or `exclude_groups` is `True`, the
        function also needs to query the size of each `Group`, which may take
        a while (perhaps a minute).
    """
    engine, session = database.initialize(url)

    columns = Incident.total_hours, Subject.survived, Group.category, Group.id
    query = session.query(*columns).join(Group, Subject)
    df = tabulate(query)

    database.terminate(engine, session)

    if exclude_singles or exclude_groups:
        df['size'] = [Group.query.get(int(id_)).size for id_ in df.id]  # Hack
    if exclude_singles:
        df = df[df['size'] > 1]
    if exclude_groups:
        df = df[df['size'] == 1]

    if 'size' in df:
        df.drop('size', 1, inplace=True)
    df.drop('id', 1, inplace=True)

    df = df.assign(days=[total_hours.total_seconds()/3600/24
                         for total_hours in df.total_hours],
                   doa=[not survived for survived in df.survived])
    df = df[0 <= df.days]

    return df
