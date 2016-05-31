#!/usr/bin/env python3

"""
kaplanmeier
===========
Survival analysis
"""

from collections import Counter
import matplotlib.pyplot as plt
from lifelines import KaplanMeierFitter

import database
from database.models import Subject, Group, Incident
from empirical import read_data


def execute():
    df = read_data('sqlite:///../data/isrid-master.db')
    df = df.assign(hours=[total_hours.total_seconds()/3600
                          for total_hours in df.total_hours],
                   doa=[not survived for survived in df.survived])
    df = df[0 <= df.hours]

    figure, axes = plt.subplots(3, 3, figsize=(15, 10))

    categories = Counter(df.category)
    plot = 0
    for category, count in categories.most_common()[:9]:
        ax = axes[plot//3, plot%3]
        df_ = df[df.category == category]

        kmf = KaplanMeierFitter()
        kmf.fit(df_.hours, event_observed=df_.doa, label=category)
        kmf.plot(show_censors=True, censor_styles={'marker': '|', 'ms': 6},
                 ax=ax)
        ax.set_xlim(0, min(24*30, ax.get_xlim()[1]))

        ax.set_title('{}, N = {}'.format(category, len(df_)))
        ax.set_xlabel('Total Incident Time (h)')
        ax.set_ylabel('Probability of Survival')

        ax.legend_.remove()

        plot += 1

    figure.suptitle('Kaplan-Meier Empirical Survival Curves', fontsize=20)
    figure.tight_layout()
    plt.subplots_adjust(top=0.925)
    plt.savefig('../doc/figures/kaplan-meier.svg', transparent=True)
    plt.show()


if __name__ == '__main__':
    execute()
