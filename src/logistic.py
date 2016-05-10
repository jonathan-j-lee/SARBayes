#!/usr/bin/env python3

"""
logistic.py
"""

import datetime
from functools import reduce
import matplotlib.pyplot as plt
import numpy as np
import operator
import pandas as pd
import pymc as pm
from scipy.stats.mstats import mquantiles

import database
from database.models import Subject, Group, Incident, Location
from database.models import Operation, Outcome, Weather, Search


def sigmoid(x, a=0, b=-1, l=1):
    return l/(1 + np.exp(a + np.dot(b, x)))


def brier_score(observations, predictions):
    assert len(observations) == len(predictions)
    return sum(np.pow(observations - predictions, 2))/len(observations)


def read_data(url, *columns, not_null=True):
    engine, session = database.initialize(url)

    query = session.query(*columns).join(Group, Incident)
    query = query.filter(*map(lambda column: column != None, columns))

    database.terminate(engine, session)

    data = pd.DataFrame()

    for column in columns:
        name, datatype = str(column).split('.')[-1], column.type.python_type
        values = (value for value, *empty in query.from_self(column))

        if datatype == datetime.timedelta:
            datatype = float
            values = map(lambda value: value.total_seconds()/3600, values)

        data[name] = np.fromiter(values, np.dtype(datatype))

    return data


def fit(data, label, *criteria, verbose=True):
    if len(criteria) > 0:
        data = data[reduce(operator.iand, criteria)]

    times = data['search_hours'].as_matrix()
    survivals = data['survived'].as_matrix()
    starting_rate = sum(survivals)/len(survivals)

    if len(data) < 100:
        print('Not enough cases.')

    alpha = np.log(1/starting_rate - 1)
    beta = pm.Beta('beta', 1, 2, 1e-3)

    prob = pm.Lambda('prob', lambda t=times, a=alpha, b=beta: sigmoid(t, a, b))
    survival = pm.Bernoulli('survival', prob, value=survivals, observed=True)

    model = pm.Model([survival, beta])
    mcmc = pm.MCMC(model)
    mcmc.sample(12000, 10000, 2, progress_bar=verbose)

    beta_samples = mcmc.trace('beta')[:, None]
    beta_mean = np.mean(beta_samples)

    if verbose:
        print('Group:', label)
        print('  n = {}'.format(len(data)))
        print('  r = {:.3f}%'.format(100*starting_rate))
        print('  \u03b1 = {:.3f}'.format(alpha))
        print('  \u03b2 = {:.5f}'.format(beta_mean))

    return alpha, beta_samples

    """
    # histogram = plt.hist(beta_samples, 100, [0, 0.05], normed=True, alpha=0.6)
    # frequencies, ticks, patches = histogram

    time_ticks = np.linspace(0, time_max, tick_count)
    line, *_ = plt.plot(time_ticks, sigmoid(time_ticks, alpha, beta_mean),
                        label=label)
    return line, beta_mean
    """


def execute():
    data = read_data('sqlite:///../data/isrid-master.db', Subject.age,
                     Subject.sex, Incident.search_hours, Subject.survived)
    data = data[data.search_hours > 0]

    # plt.legend(handles=lines)
    plt.title('Survival Curves Over Time (Male Subjects)')
    plt.xlabel('Search Duration (hours)')
    plt.ylabel('Probability of Survival')
    plt.xlim(0, 1000)
    plt.ylim(0, 1)
    plt.show()


if __name__ == '__main__':
    execute()
