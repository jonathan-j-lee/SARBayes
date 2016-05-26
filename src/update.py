"""
update
======
"""

import datetime
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


def augment_weather_instance(weather, datetime_, ipp):
    start_date = datetime_.date()
    end_date = start_date + datetime.timedelta(1)
    fields = ['surfaceTemperatureCelsius', 'windSpeedKph',
              'precipitationPreviousHourCentimeters', 'downwardSolarRadiation']

    history = wsi.fetch_history(lat=ipp.latitude, long=ipp.longitude,
                                startDate=start_date, endDate=end_date,
                                fields=fields)

    series = history['weatherData']['hourly']['hours']

    scrub = lambda sequence: filter(lambda item: item is not None, sequence)
    collect = lambda field: map(lambda hourly: hourly.get(field, None), series)

    temperatures = list(scrub(collect('surfaceTemperatureCelsius')))
    if len(temperatures) > 0:
        if weather.low_temp is None:
            weather.low_temp = min(temperatures)
        if weather.high_temp is None:
            weather.high_temp = max(temperatures)

    wind_speeds = list(scrub(collect('windSpeedKph')))
    if len(wind_speeds) > 0 and weather.wind_speed is None:
        weather.wind_speed = round(sum(wind_speeds)/len(wind_speeds), 3)

    solar_radiation = list(scrub(collect('downwardSolarRadiation')))
    if len(solar_radiation) > 0 and weather.solar_radiation is None:
        mean = sum(solar_radiation)/len(solar_radiation)
        weather.solar_radiation = round(mean, 3)

    snow, rain = 0, 0
    for hourly in series:
        temperature = hourly.get('surfaceTemperatureCelsius', None)
        prcp = hourly.get('precipitationPreviousHourCentimeters', None)

        if temperature is not None and prcp is not None:
            if temperature <= Weather.WATER_FREEZING_POINT:
                snow += prcp
            else:
                rain += prcp

    if weather.snow is None:
        weather.snow = round(snow, 3)
    if weather.rain is None:
        weather.rain = round(rain, 3)


def augment_weather_instances(session, limit=5000, save_every=50):
    logger = logging.getLogger()
    with open('../data/config.yaml') as config_file:
        config = yaml.load(config_file.read())

    wsi.DEFAULT_PARAMETERS['userKey'] = config['wsi']['key']
    logger.info('WSI key set to: {}'.format(wsi.DEFAULT_PARAMETERS['userKey']))

    query = session.query(Weather, Incident.datetime, Operation.ipp_id)
    query = query.join(Incident, Operation)
    query = query.filter(Incident.datetime, Operation.ipp_id)

    columns = Weather.high_temp, Weather.low_temp, Weather.wind_speed
    columns += Weather.snow, Weather.rain, Weather.solar_radiation
    criteria = map(lambda column: column == None, columns)
    query = query.filter(reduce(or_, criteria))

    count = 0
    for weather, datetime_, ipp_id in query:
        ipp = session.query(Point).get(ipp_id)

        if ipp.latitude is not None and ipp.longitude is not None:
            try:
                augment_weather_instance(weather, datetime_, ipp)
                logger.info('Updated {}'.format(weather))
            except ValueError as error:
                logger.error('Instance ID {}: {}'.format(weather.id, error))
            except error:
                logger.error(error)
                break

            count += 1
            if count >= limit:
                break
            elif (count + 1)%save_every == 0:
                session.commit()

    session.commit()
    logger.info('Updated {} weather instances'.format(count))


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
