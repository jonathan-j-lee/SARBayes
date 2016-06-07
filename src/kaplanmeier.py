#!/usr/bin/env python3

"""
kaplanmeier
===========
Survival analysis
"""

from collections import Counter
import matplotlib
import matplotlib.pyplot as plt
from lifelines import KaplanMeierFitter

import database
from database.models import Subject, Group, Incident
from database.processing import tabulate


def execute():
    matplotlib.rc('font', size=20)

    engine, session = database.initialize('sqlite:///../data/isrid-master.db')

    query = session.query(Incident.total_hours, Subject.survived,
                          Group.category).join(Group, Subject)
    query = query.filter(Group.size == 1)
    df = tabulate(query)

    database.terminate(engine, session)

    df = df.assign(days=[total_hours.total_seconds()/3600/24
                         for total_hours in df.total_hours],
                   doa=[not survived for survived in df.survived])
    df = df[0 <= df.days]

    rows, columns = 2, 2
    grid, axes = plt.subplots(rows, columns, figsize=(15, 10))

    categories = Counter(df.category)
    plot = 0
    kmfs = []
    for category, count in categories.most_common()[:rows*columns]:
        ax = axes[plot//columns, plot%columns]
        df_ = df[df.category == category]

        kmf = KaplanMeierFitter()
        kmf.fit(df_.days, event_observed=df_.doa, label=category)
        kmf.plot(show_censors=True, censor_styles={'marker': '|', 'ms': 6},
                 ax=ax)
        kmfs.append(kmf)

        ax.set_xlim(0, min(30, 1.05*ax.get_xlim()[1]))
        ax.set_ylim(0, 1)

        ax.set_title('{} (N = {})'.format(category, len(df_)))
        ax.set_xlabel('Total Incident Time (days)')
        ax.set_ylabel('Probability of Survival')

        ax.legend_.remove()
        ax.grid(True)

        plot += 1

    grid.suptitle('Kaplan-Meier Survival Curves', fontsize=25)
    grid.tight_layout()
    grid.subplots_adjust(top=0.9)
    grid.savefig('../doc/figures/kaplan-meier/km-single-grid-large.svg', transparent=True)

    combined = plt.figure(figsize=(15, 10))
    ax = combined.add_subplot(1, 1, 1)
    for kmf in kmfs[:rows*columns]:
        kmf.plot(ci_show=False, show_censors=True,
                 censor_styles={'marker': '|', 'ms': 6}, ax=ax)

    ax.set_xlim(0, 15)
    ax.set_ylim(0, 1)
    ax.set_xlabel('Total Incident Time (days)')
    ax.set_ylabel('Probability of Survival')
    ax.set_title('Kaplan-Meier Survival Curves', fontsize=25)
    ax.grid(True)
    combined.savefig('../doc/figures/kaplan-meier/km-single-combined-large.svg', transparent=True)

    plt.show()


if __name__ == '__main__':
    execute()
