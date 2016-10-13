#!/usr/bin/env python3

"""
times -- Analyze the distribution of incident times.
"""

import datetime
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats
from scipy.special import i0, i1  # Modified Bessel functions

import database
from database.models import Incident
from database.processing import tabulate


def read_time_data(url):
    engine, session = database.initialize(url)
    df = tabulate(session.query(Incident.datetime))
    database.terminate(engine, session)

    df = df.assign(time=[datetime.time() for datetime in df.datetime])
    df = df[df.time != datetime.time(0)]
    df = df.assign(hour=[time.hour + time.minute/60 + time.second/3600
                         for time in df.time])

    return df


def setup_environment():
    plt.figure(figsize=(15, 10))
    plt.title('Incident Time Distribution')
    plt.xlabel('Incident Time')
    plt.ylabel('Relative Frequency')

    plt.xlim(0, 24)
    plt.ylim(0, 0.08)

    hours = range(0, 27, 3)
    labels = [datetime.time(hour%24).strftime('%I:%M %p') for hour in hours]
    plt.xticks(hours, labels, rotation=45)
    plt.tick_params(left='off', top='off', right='off', length=7.5,
                    direction='out')

    plt.grid(which='both')


def hours_to_radians(hour):
    return np.pi*(hour/12 - 1)


def radians_to_hours(radian):
    return 12*(radian/np.pi + 1)


def estimate_distribution(hours):
    theta = hours_to_radians(hours)
    z = np.vectorize(complex)(np.cos(theta), np.sin(theta))
    n = len(z)

    z_mean = np.mean(z)
    mu = np.arctan2(z_mean.imag, z_mean.real)

    r2 = np.mean(z.real)**2 + np.mean(z.imag)**2
    re = np.sqrt(n/(n - 1)*(r2 - 1/n))

    x = np.arange(0, 10, 1e-4)
    y = np.abs(i1(x)/i0(x) - re)
    kappa = x[np.argmin(y)]

    return mu, kappa


def plot_histogram(values, label=None):
    plt.hist(values, 48, [0, 24], True, alpha=0.3, label=label)


def plot_pdf(mu, kappa):
    x = np.linspace(-np.pi, np.pi, pow(10, 3))
    pdf = lambda x: np.exp(kappa*np.cos(x - mu))/(2*np.pi*i0(kappa))
    label = 'Fitted von Mises PDF ($\mu = {:.3f}\:h$, $\kappa = {:.3f}\:h$)'
    plt.plot(radians_to_hours(x), np.pi*pdf(x)/12, alpha=0.6,
             label=label.format(*map(radians_to_hours, [mu, kappa])))


def execute():
    df = read_time_data('sqlite:///../data/isrid-master.db')
    hours = df.hour.as_matrix()
    mu, kappa = estimate_distribution(hours)
    samples = radians_to_hours(np.random.vonmises(mu, kappa, pow(10, 6)))

    setup_environment()
    plot_histogram(hours, 'Empirical Data (N = {})'.format(len(hours)))
    plot_histogram(samples, '$10^6$ Samples from Fitted Distribution')
    plot_pdf(mu, kappa)

    plt.legend()
    plt.savefig('../doc/figures/incident-time-distribution/'
                'incident-time-distribution.svg', transparent=True)
    plt.show()


if __name__ == '__main__':
    execute()
