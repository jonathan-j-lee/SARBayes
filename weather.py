#!/usr/bin/env python3
# weather.py

"""
SARbayes
================================================================================
The purpose of this module is to provide access to historic weather data using 
the API of the National Centers for Environmental Information (NCEI).

The API provides the following endpoints: 
  * datasets
  * datacategories
  * datatypes
  * locationcategories
  * locations
  * stations
  * data

Every call to the API yields JSON data, with one key for results and the other 
for metadata like so: 

    {
        "results": ..., 
        "metadata": {
            "resultset": {
                "limit": ..., 
                "count": ..., 
                "offset": ...
            }
        }
    }

The maximum number of results that can be requested per call is 1000. The 
default limit is 25 items.

The full documentation is at "http://www.ncdc.noaa.gov/cdo-web/webservices/v2".
================================================================================
"""

import urllib.request, urllib.parse
import geopy
import json
from math import pi, sin, cos, asin, degrees, radians
import numpy as np

API_URL = 'http://www.ncdc.noaa.gov/cdo-web/api/v2/{}?{}'
API_TOKEN = 'CAKlHptoFxCtALqpfyjIKtmpfCbQIWse'

R = 6371  # Earth's radius in km


def request_data(endpoint, safe=':,', **parameters):
    """ Build the URL and fetch the data. """
    url = API_URL.format(endpoint, 
        urllib.parse.urlencode(parameters, safe=safe))
    request = urllib.request.Request(url, headers={'token': API_TOKEN})
    response = urllib.request.urlopen(request)
    raw_data = json.loads(response.read().decode('utf-8'))
    return raw_data


def get_bounds(coordinates, d):
    """ Calculate the southwest and northeast coordinates of a bounding box.
        Let 2d be the length of each of the sides of the box.
        
        Sources: 
          * http://janmatuschek.de/LatitudeLongitudeBoundingCoordinates
          * https://github.com/jfein/PyGeoTools/blob/master/geolocation.py
    """
    lat, lon = radians(coordinates.latitude), radians(coordinates.longitude)
    r = d/R
    
    lat_min, lat_max = lat - r, lat + r
    # Special case: poles
    if abs(lat_min) > pi/2:
        lon_min, lon_max = -pi, pi
        lat_min, lat_max = max(lat_min, -pi/2), min(lat_max, pi/2)
    else:
        change_lon = asin(sin(r)/cos(lat))
        lon_min, lon_max = lon - change_lon, lon + change_lon
        if lon_min < -pi:
            lon_min += 2*pi
        if lon_max > pi:
            lon_max -= 2*pi
    
    return (
        geopy.Point(degrees(lat_min), degrees(lon_min)), 
        geopy.Point(degrees(lat_max), degrees(lon_max))
    )


def get_stations(date, coordinates, datasetid='GHCND', d=20):
    """ Get the data of the weather stations available at the given date and 
        coordinates within a bounding box with sides of length 2d (d in km).
    """
    date_as_str = date.date().isoformat()
    sw, ne = get_bounds(coordinates, d)
    extent = '{},{},{},{}'.format(
        sw.latitude, sw.longitude, ne.latitude, ne.longitude)
    
    raw_data = request_data(
        'stations', 
        datasetid=datasetid, 
        startdate=date_as_str, 
        enddate=date_as_str, 
        extent=extent
    )
    
    if 'results' in raw_data:
        for station in raw_data['results']:
            yield station


def get_conditions(date, coordinates, datasetid='GHCND'):
    """ Get the weather conditions at a given date and location.
        Returns as a dictionary: 
          * Maximum temperature (tenths of degrees C)
          * Minimum temperature (tenths of degrees C)
          * Average daily wind speed (m/s)
          * Precipitation (mm)
          * Snowfall (mm)
    """
    date_as_str = date.date().isoformat()
    required_data = {
        data_type: [] for data_type in ['TMAX', 'TMIN', 'AWND', 'PRCP', 'SNOW']
    }
    
    stations = get_stations(date, coordinates)
    raw_data = request_data(
        'data', 
        datasetid=datasetid, 
        startdate=date_as_str, 
        enddate=date_as_str, 
        # Clarification: the documentation says that stationids should be 
        # ampersand-separated. This is wrong. They should be comma-separated.
        stationid=','.join(station['id'] for station in stations), 
        limit=1000
    )
    
    if 'results' in raw_data:
        for measurement in raw_data['results']:
            try:
                data_type, value = measurement['datatype'], measurement['value']
                print(data_type)
                if data_type in required_data:
                    required_data[data_type].append(float(value))
            except ValueError:  # The value was not a float
                pass
    
    for data_type, values in required_data.items():
        required_data[data_type] = np.average(values) if values else None
    
    return required_data
