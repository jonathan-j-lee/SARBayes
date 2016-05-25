"""
weather.noaa
============
"""

__all__ = ['fetch', 'fetch_history']

import datetime
import json
from urllib.request import Request, urlopen, urljoin
from urllib.parse import urlencode

API_TOKEN = None

BASE_URL = 'http://www.ncdc.noaa.gov/cdo-web/api/v2/'

ENDPOINTS = ('datasets', 'datacategories', 'datatypes', 'locationcategories',
             'locations', 'stations', 'data')


def fetch(endpoint, safe=':,', **parameters):
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
    stations = fetch('stations', datasetid='GHCND', startdate=date,
                     enddate=date, datatypeid=datatypes, extent=bounds,
                     limit=1000)

    identifiers = [station['id'] for station in stations['results']]

    data = fetch('data', datasetid='GHCND', startdate=date, enddate=date,
                 datatypeid=datatypes, stationid=identifiers, limit=1000)

    return {datatype: [record['value'] for record in data['results']
                  if record['datatype'] == datatype] for datatype in datatypes}
