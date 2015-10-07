#!/usr/bin/env python3
# SARbayes/src/database/cleansing.py

"""
database/cleansing.py
"""


import decimal
import fractions
import datetime
import re


def format_int(raw_value):
    if isinstance(raw_value, int):
        return raw_value
    else:
        pass


def format_str(raw_value):
    if isinstance(raw_value, str):
        return raw_value
    else:
        print(raw_value)


def format_datetime(raw_value):
    if isinstance(raw_value, datetime.datetime):
        return raw_value
    elif isinstance(raw_value, datetime.date):
        return datetime.datetime(raw_value.year, raw_value.month, raw_value.day)
    elif isinstance(raw_value, (int, float)):
        return datetime.datetime.fromtimestamp(raw_value)
    elif isinstance(raw_value, str):
        print(raw_value)
