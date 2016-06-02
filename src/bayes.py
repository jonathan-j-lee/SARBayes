#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
import Orange
from pomegranate import *

import database
from database.models import Subject, Group, Incident, Weather
from database.processing import survival_rate, tabulate, export_as_orange


engine, session = database.initialize('sqlite:///../data/isrid-master.db')

query = session.query(Subject.survived, Group.size, Weather.avg_temp)
query = query.join(Group, Incident, Weather)
df = tabulate(query, [True, True, True])

database.terminate(engine, session)


print(sum(df.survived)/len(df))
