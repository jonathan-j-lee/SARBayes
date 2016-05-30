#!/usr/bin/env python3

"""
shell
=====
Interactive REPL shell (read-eval-print loop).
"""

import datetime
import matplotlib.pyplot as plt
import numpy as np
import readline
from sqlalchemy import func
import yaml

import database
from database.models import Subject, Group, Incident, Location, Point
from database.models import Operation, Outcome, Weather, Search
from database.processing import survival_rate, tabulate
import weather


def loop():
    with open('../data/config.yaml') as config_file:
        config = yaml.load(config_file.read())

    weather.wsi.DEFAULT_PARAMETERS['userKey'] = config['wsi']['key']
    weather.noaa.API_TOKEN = config['noaa']['key']

    engine, session = database.initialize('sqlite:///../data/isrid-master.db')
    print('Shell initialized at: {}'.format(datetime.datetime.now()))

    cmd = 1
    while True:
        try:
            print(' =>', eval(input('[!] ')))
        except (KeyboardInterrupt, EOFError):
            print()
            break
        except Exception as error:
            print(' => {}: {}'.format(type(error).__name__, error))
        finally:
            cmd += 1

    database.terminate(engine, session)


if __name__ == '__main__':
    loop()
