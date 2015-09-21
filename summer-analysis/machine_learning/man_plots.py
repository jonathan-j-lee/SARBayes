#!/usr/bin/env python3

# 0.2149*high_temp + 86.18
# 0.2416*low_temp + 88.37
# -0.03717*wind_speed + 90.77


import math
import matplotlib.pyplot as plt
import numpy as np
import Orange


data = Orange.data.Table('ISRID-survival')
print(len(data))

_X, _Y = [], []
for instance in data:
    temp_high = instance['rain']
    status = instance.get_class()
    if not math.isnan(temp_high):
        _X.append(float(temp_high))
        _Y.append(0.0 if status._value == 1.0 else 1.0)

print(len(_X), len(_Y))

n_bins = 100
X, Y, W = [], [], []

x_bounds = np.linspace(min(_X), max(_X) + 0.1, n_bins + 1)
for index in range(len(x_bounds) - 1):
    x_lowerbound, x_upperbound = x_bounds[index], x_bounds[index + 1]
    X.append([])
    Y.append([])
    W.append(0)
    for x, y in zip(_X, _Y):
        if x_lowerbound <= x < x_upperbound:
            X[-1].append(x)
            Y[-1].append(y)
            W[-1] += 1

indices = [index for index, _X in enumerate(X) if _X]
X, Y = [np.mean(_X) for _X in X if _X], [np.mean(_Y)*100 for _Y in Y if _Y]
W = [W[index] for index in indices]
print(sum(W))

m, b = np.polyfit(X, Y, 1, w=W)
reg_fn = np.poly1d((m, b))
print(reg_fn)

plt.title('Survival Rate vs. Age')
plt.ylabel('Survival Rate (percent)')
plt.xlabel('Age (years)')
plt.scatter(X, Y, W)
plt.plot(X, reg_fn(np.array(X)))
plt.ylim(0, 100)
# Use for age, snowfall, rainfall
# plt.xlim(0, plt.xlim()[1])
plt.show()
