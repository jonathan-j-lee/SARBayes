"""
anomaly
=======
Anomaly detection.
"""


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

    k_distances = [distances[a, neighbors[a][k - 1]] for a in range(len(x))]
    reach_distances = [[(None if a == b else max(k_distances[b], distances[a, b])) for b in range(len(x))] for a in range(len(x))]
    lrds = [1/(sum(reach_distances[a][b] for b in neighbors[a])/len(neighbors[a])) for a in range(len(x))]
    lofs = [sum(lrds[u] for u in neighbors[a])/len(neighbors[a]) for a in range(len(x))]

    return lambda u: lofs[u]
