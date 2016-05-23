"""
weather.noaa
============
"""

__all__ = ['fetch']

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
        if isinstance(value, datetime.datetime):
            parameters[key] = value.strftime('%Y-%m-%d')

        elif isinstance(value, (list, tuple)):
            parameters[key] = ','.join(map(str, value))

        elif not isinstance(value, str):
            parameters[key] = str(value)

    url = urljoin(BASE_URL, endpoint) + '?' + urlencode(parameters, safe=safe)
    request = Request(url, headers={'token': API_TOKEN})

    response = urlopen(request)
    return json.loads(response.read().decode('utf-8'))
