"""
weather.wsi -- WSI historical weather data API access

This module provides access to Weather Service International's online historic
weather data API.
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
    """
    Fetch past weather measurements.

    Arguments:
        safe: A string containing characters exempt from URL encoding.
        parameters: A variable number of keyword arguments containing URL
                    parameters (overrides `DEFAULT_PARAMETERS`).

    More information on the parameters is available in the API's internal
    documentation.

    Returns:
        The response as a dictionary for JSON, `csv.reader` object for CSV, or
        an `xml.etree.ElementTree` instance for XML.

    Raises:
        ValueError: when the reponse format is unrecognizable (valid options
                    are JSON, CSV, and XML).
    """
    default = dict(DEFAULT_PARAMETERS)
    default.update(parameters)
    parameters = default

    for key, value in parameters.items():
        if isinstance(value, (datetime.datetime, datetime.date)):
            parameters[key] = value.strftime('%m/%d/%Y')

        elif isinstance(value, (list, tuple)):
            parameters[key] = ','.join(map(str, value))

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
