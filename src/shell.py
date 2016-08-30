#!/usr/bin/env python3

"""
shell -- Interactive REPL shell (read-eval-print loop).
"""

import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import Orange
import readline
from sqlalchemy import func

import database
from database.models import Subject, Group, Incident, Location, Point
from database.models import Operation, Outcome, Weather, Search
from database.processing import survival_rate, tabulate, export_to_orange
import weather
from util import configure_api_access


def loop():
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


def execute():
    configure_api_access('../data/config.yaml')
    loop()


if __name__ == '__main__':
    execute()
