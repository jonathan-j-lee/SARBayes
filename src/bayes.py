#!/usr/bin/env python3

"""
bayes
=====
"""

import logging
import matplotlib.pyplot as plt
import numpy as np
import pymc as pm

import database
from database.models import Subject, Group, Incident
from database.processing import survival_rate
from merge import initialize_logging


# Read data

initialize_logging('../logs/bayes.log', 'w+')
engine, session = database.initialize('sqlite:///../data/isrid-master.db')
logger = logging.getLogger()

subjects = session.query(Subject).filter(Subject.survived != None, Subject.weight != None)

weights = np.fromiter((subject.weight for subject in subjects), np.float64)
survivals = np.fromiter((subject.survived for subject in subjects), np.bool)

alpha = pm.Normal('alpha', mu=0, tau=1e-3, value=0)
beta = pm.Normal('beta', mu=0, tau=1e-3, value=0)

@pm.deterministic
def weight(weight=weights, alpha=alpha, beta=beta):
    return 1/(1 + np.exp(alpha + beta*weight))

survival = pm.Bernoulli('survival', weight, value=survivals, observed=True)

model = pm.Model([survivals, beta, alpha])
map_ = pm.MAP(model)
map_.fit()
mcmc = pm.MCMC(model)
mcmc.sample(iter=20000, burn=15000, thin=2)

def logistic(x, alpha, beta):
    return 1/(1 + np.exp(np.dot(beta, x) + alpha))

# Sample and flatten
alphas, betas = mcmc.trace('alpha')[:, None], mcmc.trace('beta')[:, None]
alphas = alphas.flatten()
betas = betas.flatten()

plt.scatter(weights, survivals)
weights.sort()
plt.plot(weights, logistic(weights, np.mean(alphas), np.mean(betas)), 'g')

plt.xlabel('Weight (kg)')
plt.ylabel('Probability of Survival')
plt.title('Weight Logistic Curve using Bayesian Inference')

plt.xlim(0, max(weights) + 10)
plt.ylim(0, 1)
plt.grid(True)
plt.show()

database.terminate(engine, session)
