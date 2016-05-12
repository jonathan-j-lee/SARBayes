"""
weather.noaa
============
"""

__all__ = ['fetch']

import json
from urllib.request import Request, urlopen, urljoin
from urllib.parse import urlencode

BASE_URL = 'http://www.ncdc.noaa.gov/cdo-web/api/v2/'

ENDPOINTS = ('datasets', 'datacategories', 'datatypes', 'locationcategories',
             'locations', 'stations', 'data')


def fetch_json():
    ...
