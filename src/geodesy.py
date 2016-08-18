"""
gis.geodesy -- Geodetic Data Manipulation

Notes:
  - The reference coordinate system is decimal latitude and longitude.
  - A negative latitude points south, a negative longitude west.
  - This library uses the WGS84 datum.
  - Currently, UTM calculations do not handle nonstandard zones.

Sources:
  - http://www.uwgb.edu/dutchs/usefuldata/utmformulas.htm
  - https://en.wikipedia.org/wiki/
        Universal_Transverse_Mercator_coordinate_system
  - https://en.wikipedia.org/wiki/Public_Land_Survey_System
"""

from math import (degrees, radians, sin, cos, tan, asin, acos, atan2, sinh,
                  cosh, tanh, asinh, acosh, atanh, sqrt, hypot, ceil, floor)

__all__ = [
    'from_utm',
    'to_utm',
    'from_dms',
    'to_dms',
    'great_circle',
    'bounding_box'
]

# Constants
a, f = 6378.137, 1/298.257223563    # Equatorial radius (km) and flattening
k0, easting_ = 0.9996, 500          # Point scale factor and false easting

# Derived values
n = f/(2 - f)
A = a/(1 + n)*(1 + pow(n, 2)/4 + pow(n, 4)/64)
alpha = (
    n/2 - 2/3*pow(n, 2) + 5/16*pow(n, 3),
    13/48*pow(n, 2) - 3/5*pow(n, 3),
    61/240*pow(n, 3)
)
beta = (
    n/2 - 2/3*pow(n, 2) + 37/96*pow(n, 3),
    pow(n, 2)/48 + pow(n, 3)/15,
    17/480*pow(n, 3)
)
delta = (
    2*n - 2/3*pow(n, 2) - 2*pow(n, 3),
    7/3*pow(n, 2) - 8/5*pow(n, 3),
    56/15*pow(n, 3)
)


def from_utm(easting: float, northing: float,
                zone: int, hemisphere: int =1) -> (float, float):
    """
    Convert UTM coordinates to decimal latitude and longitude coordinates.

    Keyword Arguments:
        easting: The easting in m.
        northing: The northing in m.
        zone: The zone, between 1 and 60, inclusive.
        hemisphere: A signed number, where a negative number indicates the
            coordinates are located in the southern hemisphere.

    Returns:
        latitude: The latitude, in decimal degrees.
        longitude: The longitude, in deciaml degrees.

    Raises:
        OverflowError: The coordinate does not exist.
    """
    easting, northing = easting/1000, northing/1000
    northing_ = 10000 if hemisphere < 0 else 0

    xi_ = xi = (northing - northing_)/(k0*A)
    eta_ = eta = (easting - easting_)/(k0*A)
    for j in range(1, 4):
        p, q = 2*j*xi, 2*j*eta
        xi_ -= beta[j - 1]*sin(p)*cosh(q)
        eta_ -= beta[j - 1]*cos(p)*sinh(q)

    chi = asin(sin(xi_)/cosh(eta_))
    latitude = chi + sum(delta[j - 1]*sin(2*j*chi) for j in range(1, 4))
    longitude_ = radians(6*zone - 183)
    longitude = longitude_ + atan2(sinh(eta_), cos(xi_))
    return degrees(latitude), degrees(longitude)


def to_utm(latitude: float, longitude: float) -> (float, float, int, int):
    """
    Converts decimal latitude and longitude coordinates to UTM coordinates.

    Keyword Arguments:
        latitude: The latitude, in decimal degrees.
        longitude: The longitude, in decimal degrees.

    Returns:
        easting: The easting in m.
        northing: The northing in m.
        zone: The zone, between 1 and 60, inclusive.
        hemisphere: A signed number, where a negative number indicates the
            coordinates are located in the southern hemisphere.

    Raises:
        OverflowError: The coordinate does not exist.
    """
    if abs(latitude) > 84:
        raise ValueError('Polar regions not covered')

    zone = 1 + floor((longitude + 180)/6)
    latitude, longitude = radians(latitude), radians(longitude)
    longitude_ = radians(6*zone - 183)

    p = 2*sqrt(n)/(1 + n)
    t = sinh(atanh(sin(latitude)) - p*atanh(p*sin(latitude)))
    xi_ = atan2(t, cos(longitude - longitude_))
    eta_ = atanh(sin(longitude - longitude_)/hypot(1, t))

    sigma, tau, u, v = 1, 0, 0, 0
    for j in range(1, 4):
        p, q = 2*j*xi_, 2*j*eta_
        sigma += 2*j*alpha[j - 1]*cos(p)*cosh(q)
        tau += 2*j*alpha[j - 1]*sin(p)*sinh(q)
        u += alpha[j - 1]*cos(p)*sinh(q)
        v += alpha[j - 1]*sin(p)*cosh(q)

    hemisphere = -1 if latitude < 0 else 1
    northing_ = 10000 if hemisphere < 0 else 0
    easting = easting_ + k0*A*(eta_ + 0)
    northing = northing_ + k0*A*(xi_ + 0)
    return 1000*easting, 1000*northing, zone, hemisphere


def from_dms(degrees: float, minutes: float, seconds: float,
        sign: int =1) -> (float):
    """
    Converts degree, minute, and second components to a decimal angle.

    Keyword Arguments:
        degrees: The number of degrees.
        minutes: The number of minutes.
        seconds: The number of seconds.
        sign: A positive or negative integer indicating the sign of the angle.

    Returns:
        decimal: The number of degrees as as single decimal.
    """
    sign = -1 if sign < 0 else 1
    return sign*(abs(degrees) + abs(minutes)/60.0 + abs(seconds)/3600.0)


def to_dms(decimal: float) -> (float, float, float, int):
    """
    Converts a decimal angle to degree, minute, and second components.

    Keyword Arguments:
        decimal: The number of degrees as as single decimal.

    Returns:
        degrees: The number of degrees.
        minutes: The number of minutes.
        seconds: The number of seconds.
        sign: A positive or negative integer indicating the sign of the angle.
    """
    sign, decimal = (-1 if decimal < 0 else 1), abs(decimal)
    degrees, minutes = decimal//1.0, 60*(decimal%1.0)
    minutes, seconds = minutes//1.0, 60*(minutes%1.0)
    return degrees, minutes, seconds, sign


def great_circle(latitude1: float, longitude1: float,
        latitude2: float, longitude2: float) -> (float):
    """
    Calculate the angle between two points on the surface of a sphere.
    Multiply this angle by the sphere's radius to obtain the distance along the
    surface between the two points.

    Keyword Arguments:
        latitude1: The latitude of the first point, in decimal degrees.
        longitude1: The longitude of the first point, in decimal degrees.
        latitude2: The latitude of the second point, in decimal degrees.
        longitude2: The longitude of the second point, in decimal degrees.

    Returns:
        angle: The angle between the two points.
    """
    latitude1, latitude2 = radians(latitude1), radians(latitude2)
    delta = radians(abs(longitude1 - longitude2))

    p = sin(latitude1)*sin(latitude2)
    q = cos(latitude1)*cos(latitude2)*cos(delta)
    return degrees(acos(p + q))


def bounding_box(latitude: float, longitude: float, side: float) -> (
        float, float, float, float):
    """
    Calculate the southwest and northeast coordinates of a bounding box.

    Keyword Arguments:
        latitude: The latitude of the center of the box, in decimal degrees.
        longitude: The longitude of the center of the box, in decimal degrees.
        side: The length of each side of the box.

    Returns:
        south: The latitude of the southern bound of the box.
        west: The longitude of the western bound of the box.
        north: The latitude of the northern bound of the box.
        east: The longitude of the eastern bound of the box.
    """
    raise NotImplementedError
