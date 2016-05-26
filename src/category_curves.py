from anomaly import local_outlier_factors
from collections import Counter
import matplotlib.pyplot as plt
import pymc as pm
import numpy as np
from scipy.stats.mstats import mquantiles
from sqlalchemy import func

import database
from database.models import Subject, Group, Incident
from logistic import sigmoid


engine, session = database.initialize('sqlite:///../data/isrid-master.db')

query = session.query(Group.category, Incident.total_hours, Subject.survived)
query = query.join(Incident, Subject)
query = query.filter(Group.category != None, Incident.total_hours != None,
                     Subject.survived != None)

database.terminate(engine, session)


subquery = query.from_self(Group.category)
frequencies = Counter((category.strip().upper() for category, *_ in subquery))
categories = sorted(frequencies, key=lambda category: -frequencies[category])


figure, axes = plt.subplots(3, 3, figsize=(15, 11))
time_max = 1000
time_ticks = np.linspace(0, time_max, time_max + 1)[:, None]

for row in range(3):
    for column in range(3):
        category = categories[row*3 + column]
        ax = axes[row, column]
        print(category)

        subquery = query.filter(func.upper(Group.category) == category)
        subquery = subquery.filter(Incident.total_hours > 0)
        subquery = subquery.order_by(Incident.total_hours.asc())

        times = subquery.from_self(Incident.total_hours).all()
        times = list(map(lambda t: t[0].total_seconds()/3600, times))
        survivals = subquery.from_self(Subject.survived).all()
        survivals = [survival for survival, *_ in survivals]

        indices = []
        lof = local_outlier_factors(times)
        for index, time in enumerate(times):
            if time > 21*24:
                indices.append(index)
            elif lof(index) > 100:
                indices.append(index)

        print('Removing {} outliers'.format(len(indices)))
        times = [time for index, time in enumerate(times)
                 if index not in indices]
        survivals = [survival for index, survival in enumerate(survivals)
                     if index not in indices]

        alpha = np.log(1/0.99 - 1)
        beta = pm.Beta('beta', 1, 2, 1e-3)
        prob = pm.Lambda('prob', lambda t=times, a=alpha, b=beta:
                         sigmoid(t, a, b))
        survival = pm.Bernoulli('survival', prob, value=survivals,
                                observed=True)

        model = pm.Model([survival, beta])
        mcmc = pm.MCMC(model)
        mcmc.sample(12000, 10000, 2)

        beta_samples = mcmc.trace('beta')[:, None]

        label = 'N = {}'.format(subquery.count())
        y = sigmoid(time_ticks.T, alpha, beta_samples)
        line, *_ = ax.plot(time_ticks, y.mean(axis=0), label=label)

        quantiles = mquantiles(y, [0.025, 0.975], axis=0)
        ax.fill_between(time_ticks[:, 0], *quantiles, alpha=0.25,
                        color=line.get_color())

        quantiles = mquantiles(y, [0.25, 0.5, 0.75], axis=0)
        for quantile in quantiles:
            ax.plot(time_ticks, quantile, 'g--')

        centers, probabilities = [], []
        bins = list(range(0, len(times), 20)) + [len(times)]
        for lowerbound, upperbound in zip(bins[:-1], bins[1:]):
            centers.append(np.mean(times[lowerbound:upperbound]))
            probabilities.append(np.mean(survivals[lowerbound:upperbound]))

        ax.scatter(centers, probabilities)
        ax.set_title('{}, {}'.format(category, label))
        ax.set_xlabel('Total Incident Time (h)')
        ax.set_ylabel('Probability of Survival')
        ax.set_xlim(0, time_max)
        ax.set_ylim(0, 1)

figure.suptitle('Survival Curves by Category', fontsize=20)
figure.tight_layout()
plt.subplots_adjust(top=0.925)
plt.savefig('../doc/figures/survival-curves-category.svg', transparent=True)
plt.savefig('../doc/figures/survival-curves-category.png', transparent=True,
            dpi=100)
plt.show()
