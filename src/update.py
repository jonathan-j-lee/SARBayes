"""
update
======
"""

from functools import reduce
import logging
from sqlalchemy import or_

import database
from database.models import Subject, Group, Incident, Location, Point
from database.models import Operation, Outcome, Weather, Search
from merge import initialize_logging


def delete_case(session, incident_id):
    deletions = []

    for model in Group, Location, Operation, Outcome, Weather, Search:
        query = session.query(model).filter(model.incident_id == incident_id)
        instance = query.one()

        if model == Group:
            deletions += instance.subjects
        elif model == Operation:
            deletions += [instance.ipp, instance.dest, instance.revised_point]
        elif model == Outcome:
            deletions += [instance.dec_point, instance.find_point]
        deletions.append(instance)

    for instance in deletions:
        if instance is not None:
            session.delete(instance)


def remove_unreadable_incidents(session, limit=float('inf'), save_every=100):
    logger, count = logging.getLogger(), 0

    for incident_id, *empty in session.query(Incident.id):
        query = session.query(Incident).filter(Incident.id == incident_id)

        try:
            query.one()
        except ValueError:
            logger.info('Removing incident {} ... '.format(incident_id))
            delete_case(session, incident_id)
            query.delete()

            count += 1
            if count >= limit:
                break
            # elif (count + 1)%save_every == 0:
            #     session.commit()

    session.commit()
    logger.info('Removed {} cases'.format(count))


def add_missing_instances(session):
    # for incident in session.query(Incident):
    #     print(incident)

    # session.commit()
    ...


def augment_weather_instance(weather):
    logger = logging.getLogger()
    logger.debug(weather)


def augment_weather_instances(session, limit=500, save_every=10):
    # criteria = reduce(or_, map(lambda column: column == None, column_map.values()))
    # print(criteria)

    """
    count = 0
    for weather in session.query(Weather):
        modified = augment_weather_instance(weather)

        if modified:
            count += 1
            if count >= limit:
                break

        if (count + 1)%save_every == 0:
            session.commit()

    session.commit()
    """


def execute():
    initialize_logging('../logs/update.log')
    logger = logging.getLogger()
    engine, session = database.initialize('sqlite:///../data/isrid-master.db')

    tasks = [remove_unreadable_incidents, add_missing_instances,
             augment_weather_instances]

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
