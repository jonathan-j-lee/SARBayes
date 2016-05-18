"""
update
======
"""

from functools import reduce
import logging
from sqlalchemy import or_
import yaml

import database
from database.models import Subject, Group, Incident, Location, Point
from database.models import Operation, Outcome, Weather, Search
from merge import initialize_logging
from weather import wsi


def remove_unreadable_incidents(session, limit=float('inf'), save_every=100):
    logger, count = logging.getLogger(), 0

    for incident_id, *empty in session.query(Incident.id):
        query = session.query(Incident).filter(Incident.id == incident_id)

        try:
            query.one()
        except ValueError:
            logger.info('Removing incident {} ... '.format(incident_id))

            for model in Group, Weather, Location, Operation, Outcome, Search:
                subquery = session.query(model)
                subquery = subquery.filter(model.incident_id == incident_id)

                instance = subquery.one_or_none()
                if instance is not None:
                    session.delete(instance)

            query.delete()

            count += 1
            if count >= limit:
                break
            elif (count + 1)%save_every == 0:
                session.commit()

    session.commit()
    logger.info('Removed {} cases'.format(count))


def add_missing_instances(session):
    logger, count = logging.getLogger(), 0

    ...


def augment_weather_instance(weather, datetime, ipp):
    logger = logging.getLogger()
    logger.debug(weather)

    # wsi.fetch_history(lat=ipp.latitude, long=ipp.longitude, startDate=datetime, endDate, fields=)


def augment_weather_instances(session, limit=1000, save_every=10):
    with open('../data/config.yaml') as config_file:
        config = yaml.load(config_file.read())

    wsi.DEFAULT_PARAMETERS['userKey'] = config['wsi']['key']

    query = session.query(Weather, Incident.datetime, Operation.ipp_id)
    query = query.join(Incident, Operation)
    query = query.filter(Incident.datetime, Operation.ipp_id)

    # columns = Weather.high_temp, Weather.low_temp
    # criteria = map(lambda column: column == None, columns)
    # query = query.filter(reduce(or_, criteria))

    for weather, datetime, ipp_id in query:
        ipp = session.query(Point).get(ipp_id)
        augment_weather_instance(weather, datetime, ipp)

    session.commit()


def execute():
    initialize_logging('../logs/update.log')
    logger = logging.getLogger()
    engine, session = database.initialize('sqlite:///../data/isrid-master.db')

    tasks = [augment_weather_instances]

    for task in tasks:
        try:
            task_name = task.__name__.replace('_', ' ')
            logger.info('Starting task: {}'.format(task_name))
            task(session)

        except KeyboardInterrupt:
            print()
            logger.info('Terminating update ... ')
            break

        except Exception as error:
            logger.error('{}: {}'.format(type(error).__name__, error))
            break

    logging.shutdown()
    database.terminate(engine, session)


if __name__ == '__main__':
    execute()
