#!/usr/bin/env python3

"""
bayes
=====
"""

import logging
import matplotlib.pyplot as plt
import numpy as np
from pymc import deterministic, stochastic, observed
from pymc import Uniform, Categorical, MCMC, Normal, InvLogit, Dirichlet

import database
from database.models import Subject
from database.processing import survival_rate
from merge import initialize_logging


# Read data

initialize_logging('../logs/bayes.log', 'w+')
engine, session = database.initialize('sqlite:///../data/isrid-master.db')
logger = logging.getLogger()

subjects = session.query(Subject)
n = subjects.count()

rate = 100*survival_rate(subjects)
logger.info('Baseline survival rate: {:.3f}%'.format(rate))

database.terminate(engine, session)


# Construct model

age = Uniform('age', 0, 100, [subject.age for subject in subjects])

height = Uniform('height', 0, 250, [subject.height for subject in subjects], observed=True)
weight = Uniform('weight', 0, 250, [subject.weight for subject in subjects], observed=True)

@deterministic
def bmi(height=height, weight=weight):
    return 1e4*weight/height**2

# @stochastic
# def survival(bmi=bmi):
#     ...

# components = [age]
# model = MCMC(components)
