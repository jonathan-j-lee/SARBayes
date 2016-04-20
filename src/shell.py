#!/usr/bin/env python3

"""
shell
=====
Interactive database REPL shell (read-eval-print loop).
"""

import matplotlib.pyplot as plt
import numpy as np
import readline

import database
from database.models import Subject, Group, Point, Location, Weather
from database.models import Operation, Outcome, Search, Incident


def loop():
    engine, session = database.initialize('sqlite:///../data/isrid-master.db')

    cmd = 1
    while True:
        try:
            print(' =>', eval(input('[!] ')))
        except (KeyboardInterrupt, EOFError):
            print()
            break
        except Exception as error:
            print(' =>', error)
        finally:
            cmd += 1

    database.terminate(engine, session)


if __name__ == '__main__':
    loop()
