#!/usr/bin/env python3

"""
plots -- Plots of subject data
"""

import matplotlib.pyplot as plt

import database
from database.models import Subject
from database.processing import tabulate

## Fetch data

engine, session = database.initialize('sqlite:///../data/isrid-master.db')
query = session.query(Subject.age, Subject.weight, Subject.height)
query = query.filter(Subject.age != None)
df = tabulate(query, not_null=False)
database.terminate(engine, session)

## Make weight vs. age plot

color = '#177788'
df_filtered = df[df.weight.notnull()]
plt.figure(1)
plt.scatter(df_filtered.age, df_filtered.weight, c=color, alpha=0.5)
plt.xlim(0, df_filtered.age.max() + 5)
plt.ylim(0, df_filtered.weight.max() + 5)
plt.title('Weight vs. Age')
plt.xlabel('Age (year)')
plt.ylabel('Weight (kg)')
plt.tight_layout()
plt.savefig('../doc/figures/subject-data/weight-vs-age-plot.svg',
            transparent=True)

## Make height vs. age plot

df_filtered = df[df.height.notnull()]
plt.figure(2)
plt.scatter(df_filtered.age, df_filtered.height, c=color, alpha=0.5)
plt.xlim(0, df_filtered.age.max() + 5)
plt.ylim(0, df_filtered.height.max() + 5)
plt.title('Height vs. Age')
plt.xlabel('Age (year)')
plt.ylabel('Height (cm)')
plt.tight_layout()
plt.savefig('../doc/figures/subject-data/height-vs-age-plot.svg',
            transparent=True)

plt.show()
