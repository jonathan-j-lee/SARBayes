#!/usr/bin/env python3

"""
colormap -- Visualize survival rates for different categories and age groups

This standalone script takes subjects from the 10 most common categories, bins
subjects within each group by age (in increments of 10 years, up to 100 years),
and calculates the survival rate within each bin. Then, each bin is plotted on
a grid and colored by the survival rate.
"""

import database
from database.models import Subject, Group


def execute():
    engine, session = database.initialize('sqlite:///../data/isrid-master.db')


    database.terminate(engine, session)


if __name__ == '__main__':
    execute()
