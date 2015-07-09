#!/usr/bin/env python3
# SARbayes/weather/update.py

"""
SARbayes

This module adds missing weather data to the database.

See "help(weather)" for more information.
"""

import datetime
import geopy
import xlrd

from formatting import modify_database
import weather


def process(row, index, datemode):
    try:
        date = datetime.datetime(*xlrd.xldate_as_tuple(row[3], datemode))
    except (TypeError, xlrd.xldate.XLDateNegative):
        pass


if __name__ == '__main__':
    modify_database(
        '../ISRID-2.xlsx', '../ISRID-3.xlsx', 'ISRIDclean', process)
