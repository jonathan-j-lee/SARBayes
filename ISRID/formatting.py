#!/usr/bin/env python3
# SARbayes/ISRID/formatting.py

"""
SARbayes

Database cleaning routine (improved).
"""


import datetime
import re
import util

_NUMBER = r'([+-]?\d+\.?\d*)'
DATE = re.compile(r'{0}[/\']+{0}[/\']+{0}'.format(_NUMBER))


def _format_date(raw_date):
    if type(raw_date) is datetime.datetime:
        return raw_date
    elif type(raw_date) is str:
        #matches = re.findall(_NUMBER, raw_date)
        result = DATE.findall(raw_date)
        if result:
            util.log('>>>>>>>>>', result, raw_date)
        else:
            util.log(raw_date)
        #util.log(matches)
    
    # This entry is not worth saving.


def standardize(index, row_values, column_settings):
    try:
        date = _format_date(row_values[column_settings['date']['index']])
        lkp_ns = row_values[column_settings['lkp_ns']['index']]
        lkp_ew = row_values[column_settings['lkp_ew']['index']]
    except KeyError:
        return
    
    if date:
        assert type(date) is datetime.datetime
            #util.log('NOP', index, date)
