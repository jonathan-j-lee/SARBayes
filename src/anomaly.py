"""
anomaly
=======
Anomaly detection.
"""

import numpy as np


def local_outlier_factors(x, k=1):
    distances = {}
    for a in range(len(x)):
        for b in range(a):
            distances[a, b] = distances[b, a] = abs(x[b] - x[a])

    neighbors = []
    for a in range(len(x)):
        y = [b for b in range(len(x)) if b != a]
        y.sort(key=lambda b: distances[a, b])
        neighbors.append(y)

    k_distance = lambda a: distances[a, neighbors[a][k - 1]]
    reach_distance = lambda a, b: max(k_distance(b), distances[a, b])
    lrd = lambda a: 1/(sum(reach_distance(a, b) for b in neighbors[a])/
                       len(neighbors[a]))
    lof = lambda a: sum(map(lrd, neighbors[a]))/len(neighbors[a])/lrd(a)

    # yield from map(lof, range(len(x)))
    return lof
