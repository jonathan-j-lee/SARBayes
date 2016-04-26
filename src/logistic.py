#!/usr/bin/env python3

"""
logistic -- Logistic Survival-Over-Time Model
"""

from itertools import product
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymc as pm

import database
from database.models import Subject, Group, Incident
from database.processing import as_array


def sigmoid(x, a=0, b=-1, l=1):
    return l/(1 + np.exp(a + np.dot(b, x)))


def execute():
    engine, session = database.initialize('sqlite:///../data/isrid-master.db')

    query = session.query(Subject).join(Group, Incident).add_entity(Incident)
    query = query.filter(Subject.age != None, Subject.sex != None,
        Subject.survived != None, Incident.search_hours > 0)

    ages = np.array(query.from_self(Subject.age).all()).flatten()
    sexes = np.array(query.from_self(Subject.sex).all()).flatten()
    survivals = np.array(query.from_self(Subject.survived).all()).flatten()
    search_hours = np.array([hours.total_seconds()/3600 for hours, *_ in
                             query.from_self(Incident.search_hours)])

    database.terminate(engine, session)

    bins = np.array([0, 3, 6, 12, 15, 18, 21, 24] + list(range(30, 110, 10)))
    ages = np.digitize(ages, bins)

    lines = []
    for sex_, age_ in [(1, 3), (1, 5), (1, 7), (2, 3), (2, 5), (2, 7)]:
        indices = np.array([index for index, (age, sex) in enumerate(zip(ages,
                            sexes)) if age == age_ and sex == sex_])

        if indices.size < 100:
            print('Not enough cases')
            continue

        print('N = {}'.format(indices.size))

        search_hours_ = np.array([search_hours[index] for index in indices])
        survivals_ = np.array([survivals[index] for index in indices])

        alpha = pm.Normal('alpha', 0, 1e-3, 0)
        beta = pm.Normal('beta', 0, 1e-3, 0)

        @pm.deterministic
        def prob(time=search_hours_, alpha=alpha, beta=beta):
            return sigmoid(time, alpha, beta)

        survived = pm.Bernoulli('survived', prob, value=survivals_,
                                observed=True)

        model = pm.Model([survived, alpha, beta])
        mcmc = pm.MCMC(model)
        mcmc.sample(10000, 8000, 2)

        alpha_sample = np.mean(mcmc.trace('alpha')[:])
        beta_sample = np.mean(mcmc.trace('beta')[:])

        description = '{}, {} - {} years old'.format(
            ('Male' if sex_ == 1 else 'Female'), bins[age_ - 1], bins[age_])
        plt.scatter(search_hours_, survivals_)
        t = np.linspace(0, 28*24, 1001)
        line, = plt.plot(t, sigmoid(t, alpha_sample, beta_sample),
                        label=description)
        lines.append(line)

    plt.legend(handles=lines)

    plt.title('Survival Curves')
    plt.xlabel('Search Duration (hours)')
    plt.ylabel('Probability of Survival')

    plt.xlim(0, 28*24)
    plt.ylim(0, 1)

    plt.savefig('../doc/figures/survival-curves.svg', transparent=True)
    plt.show()

    # Add 95% CI


if __name__ == '__main__':
    execute()
