"""
weather.noaa -- NOAA historical weather data API access

This module provides access to the National Oceanic and Atmospheric
Administration's online historical weather data API. Access requires a token,
limited to 1000 requests per day. Requests sent too frequently may also be
ignored.

Also, note that it typically takes a few days for recent data to be available.

Additional documentation is available at:
    http://www.ncdc.noaa.gov/cdo-web/webservices/v2
"""

__all__ = ['fetch', 'fetch_history']

import datetime
import json
from urllib.request import Request, urlopen, urljoin
from urllib.parse import urlencode

API_TOKEN = None  # Set to a string containing a valid token

BASE_URL = 'http://www.ncdc.noaa.gov/cdo-web/api/v2/'

ENDPOINTS = ('datasets', 'datacategories', 'datatypes', 'locationcategories',
             'locations', 'stations', 'data')


def fetch(endpoint, safe=':,', **parameters):
    """
    Fetch JSON data with the given endpoint and parameters.

    Arguments:
        endpoint: The API endpoint as a string.
        safe: A string containing characters exempt from URL encoding.
        parameters: A variable number of keyword arguments containing the
                    URL parameters to send with the request.

    Returns:
        The response as a dictionary containing JSON data.

    Raises:
        ValueError: when no API token is set.
    """
    if API_TOKEN is None:
        raise ValueError('no API token found')

    for key, value in parameters.items():
        if isinstance(value, (datetime.datetime, datetime.date)):
            parameters[key] = value.strftime('%Y-%m-%d')

        elif isinstance(value, (list, tuple)):
            parameters[key] = ','.join(map(str, value))

        elif not isinstance(value, str):
            parameters[key] = str(value)

    url = urljoin(BASE_URL, endpoint) + '?' + urlencode(parameters, safe=safe)
    request = Request(url, headers={'token': API_TOKEN})

    response = urlopen(request)
    return json.loads(response.read().decode('utf-8'))


def fetch_history(date, bounds, *datatypes):
    """
    Fetch past weather measurements with the given datatypes.

    Arguments:
        date: A `datetime.date` object of the date to take measurements from.
        bounds: A 4-tuple containing the southern latitude, the western
                longitude, the northern latitude, and the eastern longitude.
                This specifies a box to request measurements from.
        datatypes: A variable number of datatype identifiers as strings. See
                   the API's "datatypes" endpoint for more information.

    Returns:
        A dictionary mapping each datatype identifier to a list of
        measurements, which may be empty in the event no stations recorded
        measurements for that datatype during the given date and at the given
        location.

    Raises:
        ValueError: when no API token is set.
    """
    stations = fetch('stations', datasetid='GHCND', startdate=date,
                     enddate=date, datatypeid=datatypes, extent=bounds,
                     limit=1000)

    identifiers = [station['id'] for station in stations['results']]

    data = fetch('data', datasetid='GHCND', startdate=date, enddate=date,
                 datatypeid=datatypes, stationid=identifiers, limit=1000)

    return {datatype: [record['value'] for record in data['results']
                  if record['datatype'] == datatype] for datatype in datatypes}
