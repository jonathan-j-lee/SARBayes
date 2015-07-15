#!/usr/bin/env python3
# SARbayes/ISRID/util.py

"""
SARbayes

Database cleaning routine (improved).
"""


import datetime
import sys


def log(*args, sep=' ', end='\n', file=sys.stdout):
    now = datetime.datetime.now()
    print('[{}]'.format(now.isoformat()), end=' ', file=file)
    print(*args, sep=sep, end=end, file=file)
