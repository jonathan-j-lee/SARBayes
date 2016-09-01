#!/usr/bin/env python3

"""
shell -- Interactive REPL shell (read-eval-print loop)

You can use this standalone script for quickly querying the database or testing
features of the framework. When executed, the script will present you with a
prompt, where you can enter expressions to be evaluated (this will not work for
statements, like `import`). You will have access to a SQLAlchemy scoped session
object, `session`, as well as all of the names imported at the start of this
file.

Here is an example:

[!] session.query(Incident).count()
 => 74968
[!] session.query(Subject).filter(Subject.age >= 18).count()  # Count adults
 => 23523
[!] len(set(session.query(Group.category).all()))  # Count unique categories
 => 746
[!] help(Subject)  # Browse the Subject model's documentation

 => None
[!] weather.noaa.fetch_history(datetime.datetime(2016, 7, 4),  # Single line
                               [38.8, -77.1, 38.9, -77.0], 'TMAX', 'TMIN')
 => {'TMIN': [200], 'TMAX': [233]}
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
    """
    Read and evaluate expressions provided by the user.
    """
    engine, session = database.initialize('sqlite:///../data/isrid-master.db')
    print('Shell initialized at: {}'.format(datetime.datetime.now()))

    cmd = 1  # You can change your prompt to include the command number
    while True:
        try:
            expression = input('[!] ').strip()
            if len(expression) == 0:
                continue
            print(' =>', eval(expression))
        except (KeyboardInterrupt, EOFError):
            print()
            break
        except Exception as error:
            print(' => {}: {}'.format(type(error).__name__, error))
        finally:
            cmd += 1

    database.terminate(engine, session)  # Cleanly shut down SQLAlchemy


def execute():
    """
    Configure online API access and then run the main REPL loop.
    """
    configure_api_access()
    loop()


if __name__ == '__main__':
    execute()
