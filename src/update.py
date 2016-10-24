#!/usr/bin/env python3

"""
update -- Update and augment the database

This is a standalone script for cleaning and augmenting the database. Each
function in this module except `execute` (which bootstraps the update process)
is a "task" that takes one argument, a SQLAlchemy scoped session, and operates
on the database. New tasks should be added to the list inside `execute` and use
the nameless logger `logging.getLogger()`.
"""

import datetime
from functools import reduce
import logging
from sqlalchemy import or_
import yaml

import database
from database.models import Subject, Group, Incident, Location, Point
from database.models import Operation, Outcome, Weather, Search
from util import initialize_logging
from weather import wsi
from util import configure_api_access


def remove_unreadable_incidents(session, limit=float('inf'), save_every=100):
    """
    Remove all cases with no data.

    Arguments:
        session: A SQLAlchemy scoped session object connected to the database.
        limit: The number of empty cases to remove at once (no limit by
               default).
        save_every: The number of cases to remove before commiting changes to
                    the database.
    """
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
    """
    Iterate through `Incident` instances and add missing child instances.

    Arguments:
        session: A SQLAlchemy scoped session object connected to the database.

    Note:
        The `merge` script already creates a full set of instances for every
        case (for instance, even if there is no weather data, `merge` will
        create a `Weather` instance for the case). Hence, this function's body
        remains incomplete--it is unnecessary.

        Nevertheless, if more data are added in the the future, there should be
        a way to ensure every case has a full suite of instances. This way, for
        example, we can assume every `Incident` has a `Group`.
    """
    logger, count = logging.getLogger(), 0

    ...


def augment_weather_instance(weather, datetime_, ipp):
    """
    Pull historical weather data from the online WSI database and attempt to
    fill in the `Weather` instance's missing fields.

    The data pulled are for the first day of the incident in hourly intervals.
    Wind speed and downward solar radiation are averaged and rounded to three
    decimal places. To determine the total snowfall and rainfall over the day,
    we check the temperature at each hour. If the surface temperature is less
    than zero degrees Celsius, we add the amount of precipitation for that hour
    to the total amount of snowfall. Otherwise, we consider the precipitation
    as rainfall.

    Arguments:
        weather: An instance of the `Weather` database model with at least one
                 missing field.
        datetime_: The date and time of the incident (named with the trailing
                   underscore to avoid clashing with the `datetime` module).
        ipp: The initial planning point (that is, coordinates) of the incident,
             represented as a `Point` instance.
    """
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
    """
    Find incomplete `Weather` instances with a location and time and attempt to
    supplement them with historical weather data from the online WSI database.

    Arguments:
        session: A SQLAlchemy scoped session object connected to the database.
        limit: The maximum number of instances to augment (this may be useful
               for complying with API daily usage limits).
        save_every: The number of instances to augment before the session
                    should commit the new data to the disk.
    """
    configure_api_access()
    logger = logging.getLogger()
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
    """
    Bootstrap the update process by wrapping the initialization and termination
    of logging and database access.

    Errors raised by tasks are caught here and logged, and the script is
    immediately killed.
    """
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

    logging.shutdown()  # Flush files
    database.terminate(engine, session)


if __name__ == '__main__':
    execute()
