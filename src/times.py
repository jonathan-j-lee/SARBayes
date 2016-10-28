#!/usr/bin/env python3

"""
times -- Plot the distribution of incident times

This standalone script attempts to fit a circular distribution to the time of
day of lost person incidents. In other words, we attempt to show when cases
tend to occur most frequently.
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
    """
    Read the time of day each incident occurred at.

    Arguments:
        url: A string representing the path to the database.

    Returns:
        A `pandas` dataframe with two columns: `time` and `hour`. `time`
        contains Python `datetime.time` objects with times at midnight filtered
        out (most of these indicate a date was available, but not time). `hour`
        is `time` in hours (a float between 0 and 24, exclusive).

        `time` is derived from `Incident.datetime`.
    """
    engine, session = database.initialize(url)
    df = tabulate(session.query(Incident.datetime))
    database.terminate(engine, session)

    df = df.assign(time=[datetime.time() for datetime in df.datetime])
    df = df[df.time != datetime.time(0)]
    df = df.assign(hour=[time.hour + time.minute/60 + time.second/3600
                         for time in df.time])

    return df


def setup_environment():
    """
    Set up the plot's title, labels, bounds, and style.
    """
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
    """
    Convert a time in hours to radians.

    Arguments:
        hour: A float between 0 and 24 representing the time of day in hours.

    Returns:
        A float betwen -pi and pi.
    """
    return np.pi*(hour/12 - 1)


def radians_to_hours(radians):
    """
    Convert a time in radians to hours.

    Arguments:
        radians: A float between -pi and pi.

    Returns:
        A float between 0 and 24 representing the time of day in hours.
    """
    return 12*(radians/np.pi + 1)


def estimate_distribution(hours):
    """
    Estimate the parameters of the von Mises distribution for the data.

    Arguments:
        hours: A NumPy array holding incident times as floats between 0 and 24.

    Returns:
        mu: The distribution's center as a float between -pi and pi.
        kappa: The distribution's measure of concentration as a float.

    More information about the von Mises distribution:
        https://en.wikipedia.org/wiki/Von_Mises_distribution
    """
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


def plot_histogram(hours, label=None):
    """
    Plot the distribution of incident times as a histogram with half-hour bins.

    Arguments:
        hours: A sequence of incident times in hours (floats between 0 and 24).
        label: A string representing the name to be attached to the histogram.
    """
    plt.hist(hours, 48, [0, 24], True, alpha=0.3, label=label)


def plot_pdf(mu, kappa):
    """
    Plot the probability density function of the von Mises distribution.

    Arguments:
        mu: The distribution's center as a float between -pi and pi.
        kappa: The distribution's measure of concentration as a float.
    """
    x = np.linspace(-np.pi, np.pi, pow(10, 3))
    pdf = lambda x: np.exp(kappa*np.cos(x - mu))/(2*np.pi*i0(kappa))
    label = 'Fitted von Mises PDF ($\mu = {:.3f}\:h$, $\kappa = {:.3f}\:h$)'
    plt.plot(radians_to_hours(x), np.pi*pdf(x)/12, alpha=0.6,
             label=label.format(*map(radians_to_hours, [mu, kappa])))


def execute():
    """
    Fit a von Mises distribution to the incident times and plot their empirical
    and fitted distributions (as well as the PDF of the fitted distribution).
    """
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
