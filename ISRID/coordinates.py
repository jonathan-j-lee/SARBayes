#!/usr/bin/env python3
# SARbayes/ISRID/coordinates.py

"""
SARbayes
================================================================================
The purpose of this module is to convert between several different geographic 
coordinate systems. Currently, this module supports: 

  * Latitude and longitude
      * Decimal
      * Degrees-minutes-seconds
  * Universal transverse mercator
  * Township and range (U.S. only) (Not Implemented)

================================================================================
"""

import math

R = 6378.137  # Earth's equatorial radius in km
f = 1/298.257223563
n = f/(2 - f)
k = 0.9996
_east = 500

# Technically an infinite series, but good enough
A = R/(1 + n)*(1 + (n**2)/4 + (n**4)/64)
alpha = (n/2 - 2/3*n**2 + 5/16*n**3, 13/48*n**2 - 3/5*n**3, 61/240*n**3)
beta = (n/2 - 2/3*n**2 + 37/96*n**3, 1/48*n**2 + 1/15*n**3, 17/480*n**3)
delta = (2*n - 2/3*n**2 - 2*n**3, 7/3*n**2 - 8/5*n**3, 56/15*n**3)


def lat_lon_to_utm(lat, lon):
    """ Converts a latitude and longitude coordinate to a UTM coordinate.
        
        Arguments: 
          * lat   : North-south coordinate in degrees
          * lon   : East-west coordinate in degrees
        
        Returns tuple: 
          * east  : Easting in km
          * north : Northing in km
          * zone  : Zone number between 1 and 60, inclusive
          * hemi  : Either a "1", which represents the northern hemisphere, or 
                    a "-1", which represents the southern hemisphere
    """
    _north = 10000 if lat < 0 else 0
    zone = 1 + (lon + 180)//6
    _lon = math.radians(6.0*zone - 183.0)
    lat, lon = math.radians(lat), math.radians(lon)
    
    c = 2*math.sqrt(n)/(1 + n)
    t = math.sinh(math.atanh(math.sin(lat)) - c*math.atanh(c*math.sin(lat)))
    _xi = math.atan(t/math.cos(lon - _lon))
    _eta = math.atanh(math.sin(lon - _lon)/math.hypot(1, t))
    
    x, y = 0, 0
    for j in range(1, 4):
        p, q = 2*j*_xi, 2*j*_eta
        x += alpha[j - 1]*math.cos(p)*math.sinh(q)
        y += alpha[j - 1]*math.sin(p)*math.cosh(q)
    
    east = _east + k*A*(_eta + x)
    north = _north + k*A*(_xi + y)
    return 1000*east, 1000*north, zone, (-1 if lat < 0 else 1)


def utm_to_lat_lon(east, north, zone, hemi):
    """ Converts a UTM coordinate to a latitude and longitude coordinate.
        
        Arguments: 
          * east  : Easting in km
          * north : Northing in km
          * zone  : Zone number between 1 and 60, inclusive
          * hemi  : A signed number, where a positive number represents the 
                    northern hemisphere, and a negative number represents the 
                    southern hemisphere
        
        Returns tuple: 
          * lat   : North-south coordinate in degrees
          * lon   : East-west coordinate in degrees
    """
    _north = 10000 if hemi < 0 else 0
    _lon = math.radians(6.0*zone - 183.0)
    north, east = north//1000, east//1000
    _xi, _eta = xi, eta = (north - _north)/(k*A), (east - _east)/(k*A)
    
    for j in range(1, 4):
        p, q = 2*j*xi, 2*j*eta
        _xi -= beta[j - 1]*math.sin(p)*math.cosh(q)
        _eta -= beta[j - 1]*math.cos(p)*math.sinh(q)
    
    chi = math.asin(math.sin(_xi)/math.cosh(_eta))
    lat = chi + sum(delta[j - 1]*math.sin(2*j*chi) for j in range(1, 4))
    lon = _lon + math.atan(math.sinh(_eta)/math.cos(_xi))
    return math.degrees(lat), math.degrees(lon)


def decimal_to_dms(angle):
    """ Converts a decimal angle to degrees, minutes, and seconds. """
    signed, angle = angle < 0, abs(angle)
    m, s = divmod(3600*angle, 60)
    d, m = divmod(m, 60)
    if signed:
        d, m, s = -d, -m, -s
    return d, m, s


def dms_to_decimal(d, m, s):
    """ Converts degrees, minutes, and seconds to a decimal angle. """
    return d + m/60 + s/3600
