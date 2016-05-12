"""
weather.wsi
===========
"""

__all__ = ['fetch_history']

import csv
import datetime
import io
import json
from urllib.request import urlopen
from urllib.parse import urlencode
import xml.etree.ElementTree

BASE_URL = 'http://cleanedobservations.wsi.com/CleanedObs.svc/GetObs'

DEFAULT_PARAMETERS = {
    'version': 1,
    'format': 'json',
    'units': 'metric',
    'interval': 'hourly',
    'time': 'lwt'
}


def fetch_history(safe=':,', **parameters):
    default = dict(DEFAULT_PARAMETERS)
    default.update(parameters)
    parameters = default

    if 'fields' in parameters:
        parameters['fields'] = ','.join(map(str, parameters['fields']))

    for key, value in parameters.items():
        if isinstance(value, (datetime.datetime, datetime.date)):
            parameters[key] = value.strftime('%m/%d/%Y')

        elif not isinstance(value, str):
            parameters[key] = str(value)

    url = BASE_URL + '?' + urlencode(parameters, safe=safe)
    response = urlopen(url)
    text = response.read().decode('utf-8')

    form = parameters.get('format', None)
    if form == 'json':
        return json.loads(text)
    elif form == 'csv':
        return csv.reader(io.StringIO(text))
    elif form == 'xml':
        return xml.etree.ElementTree.parse(io.StringIO(text)).getroot()
    else:
        raise ValueError('unrecognized format')
