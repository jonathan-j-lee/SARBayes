#!/usr/bin/env python3

"""
time_analysis.py
"""

import datetime
import math
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import numpy as np
import openpyxl


def read_excel(filename, skip=1):
    workbook = openpyxl.load_workbook(filename, read_only=True)
    for worksheet in workbook:
        for index, row in enumerate(worksheet.rows):
            if index >= skip:
                yield tuple(cell.value for cell in row)


def standardize(datetime_):
    if isinstance(datetime_, datetime.datetime):
        return datetime_


def get_times(filename):
    for row in read_excel(filename):
        datetime_ = standardize(row[2])
        if datetime_ is not None:
            time = datetime_.time()
            if not (time.hour == time.minute == time.second == 0):
                yield time


def time_to_seconds(time):
    return 60*(60*time.hour + time.minute) + time.second


def seconds_to_time(seconds):
    assert 0 <= seconds < 86400
    minute, second = seconds//60, seconds%60
    hour, minute = minute//60, minute%60
    return datetime.time(int(hour), int(minute), int(second))


def average(sequence):
    return sum(sequence)/len(sequence)


def median(sequence):
    sequence = list(sorted(sequence))
    n = len(sequence)//2
    if len(sequence)%2 == 1:
        return sequence[n]
    else:
        return (sequence[n - 1] + sequence[n])/2


def stddev(sequence):
    mu = average(sequence)
    return math.sqrt(sum(pow(element - mu, 2) for element in sequence)/
        len(sequence))


def plot(times):
    plt.figure(figsize=(12, 8))
    times = [time/3600 for time in times]
    n, bins, patches = plt.hist(times, 48,
        normed=1, facecolor='green', alpha=0.6)
    # y = mlab.normpdf(bins, average(times), stddev(times))
    # plt.plot(bins, y, 'r--', linewidth=1)

    # Formatting
    plt.xlabel('Hour')
    plt.ylabel('Frequency')
    plt.title('Incident Time Distribution')
    plt.axis([0, 24, 0, 0.075])
    plt.grid(True)
    plt.savefig('time-distribution.svg', transparent=True)
    plt.show()


def main():
    times = list(map(time_to_seconds, get_times('ISRID-survival.xlsx')))
    print(len(times))
    print(seconds_to_time(average(times)).isoformat())
    print(seconds_to_time(median(times)).isoformat())
    print(seconds_to_time(stddev(times)).isoformat())
    plot(times)


if __name__ == '__main__':
    main()
