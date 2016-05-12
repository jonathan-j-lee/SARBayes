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

from anomaly import local_outlier_factors
import database
from database.models import Subject, Group, Incident, Location
from database.models import Operation, Outcome, Weather, Search


def sigmoid(x, a=0, b=-1, l=1):
    return l/(1 + np.exp(a + np.dot(b, x)))


def brier_score(observations, predictions):
    assert len(observations) == len(predictions)
    return sum(np.power(observations - predictions, 2))/len(observations)


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
        raise ValueError('Not enough cases.')

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

    # histogram = plt.hist(beta_samples, 100, [0, 0.05], normed=True, alpha=0.6)
    # frequencies, ticks, patches = histogram


def execute():
    data = read_data('sqlite:///../data/isrid-master.db', Subject.age,
                     Subject.sex, Incident.search_hours, Subject.survived)
    data = data[data.search_hours > 0]

    time_max = 1000
    time_ticks = np.linspace(0, time_max, time_max + 1)[:, None]
    data = data[(21 < data.age) & (data.age < 30) & (data.sex == 1)]

    times = data['search_hours'].as_matrix()
    lof = local_outlier_factors(times)

    indices = [index for index, time in enumerate(times) if time > 1000]
    # for index in indices:
    #     print(times[index], lof(index))

    return

    lines = []
    for cutoff in [1000, float('inf')]:
        label = 'Cutoff at {} h'.format(cutoff)
        alpha, beta_samples = fit(data, label, data.search_hours < cutoff)
        beta_mean = np.mean(beta_samples)

        data_ = data.copy() # data[data.search_hours > 1000].copy()
        predictions = sigmoid(data_['search_hours'], alpha, beta_mean)
        bs = brier_score(data_['survived'], predictions)
        print('  BS = {:.3f}'.format(bs))

        y = sigmoid(time_ticks.T, alpha, beta_samples)
        line, *_ = plt.plot(time_ticks, y.mean(axis=0),
                            label=label + ' ({:.3f})'.format(bs), alpha=0.8)
        lines.append(line)

        quantiles = mquantiles(y, [0.025, 0.975], axis=0)
        plt.fill_between(time_ticks[:, 0], *quantiles, alpha=0.6,
                         color=line.get_color())

    plt.legend(handles=lines)
    plt.title('Survival Curves Over Time (Male Subjects, 21 - 30 Years Old)')
    plt.xlabel('Search Duration (hours)')
    plt.ylabel('Probability of Survival')
    plt.xlim(0, 1000)
    plt.ylim(0, 1)
    plt.grid(True)
    # plt.savefig('../doc/figures/survival-curves-male.svg', transparent=True)
    plt.show()


if __name__ == '__main__':
    execute()
