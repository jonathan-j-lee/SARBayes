#!/usr/bin/env python3

import numpy as np
from scipy.special import i0, i1  # Modified Bessel functions
from time_analysis import get_times, time_to_seconds, seconds_to_time

times = np.array(list(map(time_to_seconds, get_times('ISRID-survival.xlsx'))))
SECONDS_IN_DAY = 24*60*60
# Map hours to radians (-pi, pi)
theta = [2*np.pi*time/SECONDS_IN_DAY - np.pi for time in times]

# Calculate some preliminary values
N = len(theta)
R2_avg = pow(sum(np.cos(theta))/N, 2) + pow(sum(np.sin(theta))/N, 2)
RE = np.sqrt(N/(N - 1)*(R2_avg - 1/N))

# Get biased estimator of kappa
x = np.arange(0, 10, 1e-4)
y = abs(i1(x)/i0(x) - RE)
kappa = x[np.argmin(y)]

import matplotlib.pyplot as plt
plt.plot(x, y)
plt.show()

# Get biased estimator of mu
z_avg = sum(map(lambda t: complex(np.cos(t), np.sin(t)), theta))/N
mu = np.arctan2(z_avg.imag, z_avg.real)

a, b = np.mean(np.cos(theta)), np.mean(np.sin(theta))
print(a, b)
print(np.arctan2(b, a), mu)
print(pow(a, 2) + pow(b, 2), R2_avg)

print('kappa = {}, mu = {}'.format(kappa, mu))
print('kappa ->', seconds_to_time(kappa/(2*np.pi)*SECONDS_IN_DAY))
print('mu ->', seconds_to_time((mu + np.pi)/(2*np.pi)*SECONDS_IN_DAY))
