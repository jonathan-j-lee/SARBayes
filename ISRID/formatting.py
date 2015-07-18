#!/usr/bin/env python3
# SARbayes/ISRID/formatting.py

"""
SARbayes

Database cleaning routine (improved).
"""


import coordinates
import datetime
import geopy
import re
import util

DATE = re.compile(r'(\d+)[/\'\"]+(\d+)[/\'\"]+(\d+)')
TIME = re.compile(r'(\d+):(\d+):?(\d+)?.?(A|P)?M?')
DECIMAL = re.compile(r'([+-]?\d+\.?\d*)')
DM = re.compile(r'(\d+)[^\d](\d+(\.|\')\d+)')
DMS = re.compile(r'(\d{1,3})[\s\'\"\-/\.]{1,2}(\d+)[^\d]{1,2}(\d+)')


def _format_date(raw_date):
    if type(raw_date) is datetime.datetime:
        return raw_date
    elif type(raw_date) is str:
        raw_date = raw_date.upper()
        try:
            result = DATE.search(raw_date)
            if result:
                month, day, year = result.groups()
                month, day, year = int(month), int(day), int(year)
                if year < 100:
                    if year > 15:
                        year += 1900
                    else:
                        year += 2000
            else:
                return
            
            # Sanity check
            assert 1900 <= year <= 2015 and 1 <= month <= 12 and 1 <= day <= 31
            
            result = TIME.search(raw_date)
            if result:
                hour, minute, second, meridiem = result.groups()
                hour, minute, second = int(hour), int(minute), \
                    0 if second is None else int(second)
                
                if meridiem == 'P':
                    hour = hour % 12 + 12
                    assert 12 <= hour < 24
                else:
                    hour %= 12
                    assert 0 <= hour < 12
            else:
                hour, minute, second = 0, 0, 0
            
            # Sanity check
            assert 0 <= minute < 60 and 0 <= second < 60
            
            date = datetime.datetime(year, month, day, hour, minute, second)
            # util.log('Converting date: "{}" -> "{}"'.format(
            #     raw_date, date.isoformat()))
            return date
        except AssertionError:
            pass


def _format_lkp(raw_key, raw_city, raw_county, raw_lkp_ns, raw_lkp_ew, index):
    assert raw_lkp_ns is not None
    lat, lon = None, None
    
    if raw_lkp_ew is None:
        if type(raw_lkp_ns) is str:
            result = DECIMAL.findall(raw_lkp_ns)
            if result:
                if len(result) == 4:
                    lat = coordinates.dms_to_decimal(float(result[0]), 
                        float(result[1]), 0)
                    lon = coordinates.dms_to_decimal(float(result[2]), 
                        float(result[3]), 0)
                    if 'S' in raw_lkp_ns:
                        lat *= -1
                    if 'W' in raw_lkp_ns:
                        lon *= -1
                elif len(result) == 6:
                    lat = coordinates.dms_to_decimal(float(result[0]), 
                        float(result[1]), float(result[2]))
                    lon = coordinates.dms_to_decimal(float(result[3]), 
                        float(result[4]), float(result[5]))
                    if 'S' in raw_lkp_ns:
                        lat *= -1
                    if 'W' in raw_lkp_ns:
                        lon *= -1
                else:
                    print(len(result), result, raw_lkp_ns, raw_key)
    else:
        if type(raw_lkp_ns) is type(raw_lkp_ew) is int:
            if 0 <= raw_lkp_ns < 1000 and 0 <= raw_lkp_ew < 1000:
                # Truncated UTM form
                if 'NY' in raw_key:
                    northing = int('4' + str(raw_county) + 
                        str(raw_lkp_ns).rjust(3, '0').ljust(5, '0'))
                    easting = int('5' + 
                        str(raw_lkp_ew).rjust(3, '0').ljust(5, '0'))
                    lat, lon = coordinates.utm_to_lat_lon(
                        easting, northing, 18, 1)
            
            elif 'NY' in raw_key:
                easting = str(raw_lkp_ns)
                if easting.startswith('18'):
                    easting, zone = easting[2:], 18
                elif easting.startswith('17'):
                    easting, zone = easting[2:], 17
                else:
                    zone = 18
                easting = int(str(int(easting)).ljust(6, '0'))
                
                northing = str(raw_lkp_ew)
                if northing.startswith('4'):
                    northing = int(northing.ljust(7, '0'))
                else:
                    northing = int(('4' + northing).ljust(7, '0'))
                
                lat, lon = coordinates.utm_to_lat_lon(
                    easting, northing, zone, 1)
        
        elif type(raw_lkp_ns) is type(raw_lkp_ew) is str:
            raw_lkp_ns, raw_lkp_ew = raw_lkp_ns.strip(), raw_lkp_ew.strip()
            
            # Degrees-minutes form
            result1, result2 = DM.search(raw_lkp_ns), DM.search(raw_lkp_ew)
            if result1 and result2:
                groups1, groups2 = result1.groups(), result2.groups()
                lat = coordinates.dms_to_decimal(float(groups1[0]), 
                    float(groups1[1].replace('\'', '.')), 0)
                lon = coordinates.dms_to_decimal(float(groups2[0]), 
                    float(groups2[1].replace('\'', '.')), 0)
            
            # Degrees-minutes-seconds form
            result1, result2 = DMS.search(raw_lkp_ns), DMS.search(raw_lkp_ew)
            if result1 and result2:
                groups1, groups2 = result1.groups(), result2.groups()
                lat = coordinates.dms_to_decimal(float(groups1[0]), 
                    float(groups1[1]), float(groups1[2]))
                lon = coordinates.dms_to_decimal(float(groups2[0]), 
                    float(groups2[1]), float(groups2[2]))
            
            # Township/range or NZMG
    
    if not (lat and lon):
        # Use city/county instead
        pass
    
    if lat and lon:
        lat, lon = round(lat, 6), round(lon, 6)
        assert -90 <= lat <= 90 and -180 <= lon <= 180
        
        # util.log('Case {}: ("{}", "{}") -> ({}, {})'.format(
        #     index, raw_lkp_ns, raw_lkp_ew, lat, lon))
    
    return lat, lon


def standardize(index, row_values, column_settings):
    try:
        raw_date = row_values[column_settings['date']['index']]
        date = _format_date(raw_date)
        assert type(date) is datetime.datetime
        row_values[column_settings['date']['index']] = date
    except (KeyError, AssertionError):
        pass
    
    try:
        raw_key = row_values[column_settings['key']['index']]
        raw_city = row_values[column_settings['city']['index']]
        raw_county = row_values[column_settings['county']['index']]
        raw_lkp_ns = row_values[column_settings['lkp_ns']['index']]
        raw_lkp_ew = row_values[column_settings['lkp_ew']['index']]
        
        if raw_lkp_ns or raw_lkp_ew:
            lat, lon = _format_lkp(
                raw_key, raw_city, raw_county, raw_lkp_ns, raw_lkp_ew, index)
            assert type(lat) is type(lon) is float
            row_values[column_settings['lkp_ns']['index']] = lat
            row_values[column_settings['lkp_ew']['index']] = lon
    except (KeyError, AssertionError):
        pass
