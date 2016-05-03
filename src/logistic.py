#!/usr/bin/env python3

"""
logistic.py
"""

import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymc as pm
from scipy.stats.mstats import mquantiles

import database
from database.models import Subject, Group, Incident


def sigmoid(x, a=0, b=-1, l=1):
    return l/(1 + np.exp(a + np.dot(b, x)))


def read_data(url):
    engine, session = database.initialize(url)

    columns = Subject.age, Subject.sex, Incident.search_hours, Subject.survived
    criteria = map(lambda column: column != None, columns)

    query = session.query(Subject).join(Group, Incident).add_entity(Incident)
    query = query.filter(*criteria)
    query = query.filter(datetime.timedelta(0) < Incident.search_hours)

    database.terminate(engine, session)

    data = pd.DataFrame()
    names = 'age', 'sex', 'time', 'survival'

    for column, name in zip(columns, names):
        values = (value for value, *empty in query.from_self(column))
        datatype = column.type.python_type

        if datatype is datetime.timedelta:
            values = map(lambda value: value.total_seconds()/3600, values)
            datatype = float

        data[name] = np.fromiter(values, np.dtype(datatype))

    return data


def execute():
    data = read_data('sqlite:///../data/isrid-master.db')

    bins = np.array(list(range(0, 24, 3)) + list(range(30, 110, 10)))
    data['age'] = np.digitize(data['age'], bins)

    t_max = 2000
    t = np.linspace(0, t_max, 1001)

    for age, sex in [(x, 1) for x in range(1, 9, 1)]:
        subset = data[(data.age == age) & (data.sex == sex)]
        times = subset['time'].as_matrix()
        survivals = subset['survival'].as_matrix()

        r = sum(survivals)/survivals.size
        print('N = {}, r = {:.3f}%'.format(len(subset), 100*r))

        alpha = np.log(1/r - 1)
        beta = pm.Beta('beta', 1, 2, 1e-3)

        @pm.deterministic
        def p(t=times, a=alpha, b=beta):
            return sigmoid(t, a, b)

        survival = pm.Bernoulli('survival', p, value=survivals, observed=True)

        model = pm.Model([survival, beta])
        mcmc = pm.MCMC(model)
        mcmc.sample(10000, 8000, 2)

        beta_samples = mcmc.trace('beta')[:, None]

        alpha_mean, beta_mean = alpha, np.mean(beta_samples)
        print('\u03b1 = {:.3f}, \u03b2 = {:.5f}'.format(alpha_mean, beta_mean))

        plt.plot(t, sigmoid(t, alpha_mean, beta_mean))

    plt.xlim(0, t_max)
    plt.ylim(0, 1)
    plt.xlabel('Search Duration (hours)')
    plt.ylabel('Probability of Survival (Male)')

    plt.savefig('../doc/figures/survival-curves-male.svg', transparent=True)
    plt.show()


if __name__ == '__main__':
    execute()
