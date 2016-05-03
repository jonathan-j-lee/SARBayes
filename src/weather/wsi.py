"""
weather.wsi
===========
"""

__all__ = []

import datetime
import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode

BASE_URL = 'http://cleanedobservations.wsi.com/CleanedObs.svc/GetObs'
TOKEN = None

DEFAULT_PARAMETERS = {
    'version': 1,
    'format': 'json',
    'units': 'metric'
}


def fetch_history(safe=':,', **parameters):
    default = dict(DEFAULT_PARAMETERS)
    default.update(parameters)
    parameters = default

    for key in parameters:
        value = parameters[key]

        if isinstance(value, (datetime.datetime, datetime.date)):
            parameters[key] = value.strftime('%m/%d/%Y')

        elif not isinstance(value, str):
            parameters[key] = str(value)

    url = BASE_URL + '?' + urlencode(parameters, safe=safe)
    response = urlopen(url)
    text = response.read().decode('utf-8')
    return json.loads(text)
