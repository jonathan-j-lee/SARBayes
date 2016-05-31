"""
Empirical Quantile Curves
"""

from collections import Counter
import math
import matplotlib.pyplot as plt
import numpy as np

import database
from database.models import Subject, Group, Incident
from database.processing import tabulate


def read_data(url):
    engine, session = database.initialize(url)

    query = session.query(Incident.total_hours, Subject.survived,
                          Group.category).join(Group, Subject)\
                          .filter(Group.size == 1)
    df = tabulate(query)

    database.terminate(engine, session)

    return df


def setup_environment():
    plt.figure(figsize=(15, 10))

    plt.title('Empirical Survival Curves')
    plt.xlabel('Total Incident Time (days)')
    plt.ylabel('Probability of Survival')

    plt.ylim(0, 1)


def plot_empirical(df, category):
    times, probabilities, counts = [], [], []
    time_max = 24*math.ceil(max(df.hours)/24)
    cutoffs = list(range(0, 48, 12)) + list(range(48, 30*24 + 1, 24))
    cutoffs.append(float('inf'))

    for lowerbound, upperbound in zip(cutoffs[:-1], cutoffs[1:]):
        df_ = df[(lowerbound <= df.hours) & (df.hours < upperbound)]
        if len(df_) > 0:
            times.append(np.mean(df_.hours)/24)
            probabilities.append(np.mean(df_.survived))
            counts.append(len(df_))

    plt.scatter(times, probabilities, alpha=0.8, s=counts)
    plt.plot(times, probabilities, alpha=0.5, label=category)


def execute():
    df = read_data('sqlite:///../data/isrid-master.db')
    df = df.assign(hours=[total_hours.total_seconds()/3600
                          for total_hours in df.total_hours])

    setup_environment()
    categories = Counter(df.category)
    for category, count in categories.most_common()[:1]:
        plot_empirical(df[df.category == category], category)

    plt.xlim(0, plt.xlim()[1])
    plt.legend()
    plt.show()


if __name__ == '__main__':
    execute()
