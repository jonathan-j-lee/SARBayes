#!/usr/bin/env python3
# SARbayes/ISRID/formatting.py

"""
SARbayes

Database cleaning routine (improved).
"""


import datetime
import re
import util

DATE = re.compile(r'(\d+)[/\'\"]+(\d+)[/\'\"]+(\d+)')
TIME = re.compile(r'(\d+):(\d+):?(\d+)?.?(A|P)?M?')
DECIMAL = re.compile(r'([+-]?\d+\.?\d*)')


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


def _format_lkp(raw_key, raw_lkp_ns, raw_lkp_ew, index):
    assert raw_lkp_ns is not None
    if raw_lkp_ew is None:
        if type(raw_lkp_ns) is str:
            result = DECIMAL.findall(raw_lkp_ns)
            if result:
                pass
                #print(len(result), result, raw_lkp_ns)
    else:
        if type(raw_lkp_ns) is type(raw_lkp_ew) is float:
            # Already in latitude, longitude form
            return raw_lkp_ns, raw_lkp_ew
        elif type(raw_lkp_ns) is type(raw_lkp_ew) is int:
            pass
        else:
            pass
    
    return None, None


def standardize(index, row_values, column_settings):
    try:
        raw_date = row_values[column_settings['date']['index']]
        date = _format_date(raw_date)
        assert type(date) is datetime.datetime
        row_values[column_settings['date']['index']] = date
    except (KeyError, AssertionError):
        pass
    
    try:
        raw_key = row_values[1]
        raw_lkp_ns = row_values[column_settings['lkp_ns']['index']]
        raw_lkp_ew = row_values[column_settings['lkp_ew']['index']]
        
        if raw_lkp_ns or raw_lkp_ew:
            lat, lon = _format_lkp(raw_key, raw_lkp_ns, raw_lkp_ew, index)
            assert type(lat) is type(lon) is float
            row_values[column_settings['lkp_ns']['index']] = lat
            row_values[column_settings['lkp_ew']['index']] = lon
    except (KeyError, AssertionError):
        pass
