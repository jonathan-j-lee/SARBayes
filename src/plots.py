#!/usr/bin/env python3

"""
plots
"""

import matplotlib.pyplot as plt
import numpy as np

import database
from database.models import Subject

engine, session = database.initialize('sqlite:///../data/isrid-master.db')
subjects = session.query(Subject)
database.terminate(engine, session)

ages = np.fromiter((subject.age for subject in subjects), np.float64)
weights = np.fromiter((subject.weight for subject in subjects), np.float64)
heights = np.fromiter((subject.height for subject in subjects), np.float64)

figure = plt.figure(figsize=(16, 8))

ax = figure.add_subplot(1, 2, 1)
ax.scatter(ages, weights, c='#2574a9', alpha=0.7)
ax.set_title('Weight vs. Age')
ax.set_xlim(0, np.nanmax(ages) + 5)
ax.set_ylim(0, np.nanmax(weights) + 5)
ax.set_xlabel('Age (year)')
ax.set_ylabel('Weight (kg)')

ax = figure.add_subplot(1, 2, 2)
ax.scatter(ages, heights, c='#2574a9', alpha=0.7)
ax.set_title('Height vs. Age')
ax.set_xlim(0, np.nanmax(ages) + 5)
ax.set_ylim(0, np.nanmax(heights) + 5)
ax.set_xlabel('Age (year)')
ax.set_ylabel('Height (cm)')

plt.savefig('../doc/figures/age-plots.svg', transparent=True)
plt.show()
