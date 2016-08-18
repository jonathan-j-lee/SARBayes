"""
anomaly -- Anomaly detection

The purpose of this module is to filter out unusually long-term survival cases
when fitting survival curves to the data.
"""


def local_outlier_factors(x, k=1):
    """
    Given a sequence `x` of real numbers, use the local density of points to
    determine what to consider an outlier.

    Source: https://en.wikipedia.org/wiki/Local_outlier_factor

    Arguments:
        x: A sequence (e.g. list, tuple, NumPy array) of real numbers to search
           outliers for.
        k: The number of neighbors to search for at each point.

    Returns:
        An anonymous function that accepts the index of an element in `x` (i.e.
        between zero and `len(x)`, inclusive) and returns the local outlier
        factor (LOF) of that element. The greater the LOF, the more likely it
        is that element is an outlier.
    """
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

    reach_distances = [[(None if a == b else
                         max(k_distances[b], distances[a, b]))
                         for b in range(len(x))] for a in range(len(x))]

    lrds = [1/(sum(reach_distances[a][b] for b in neighbors[a])/
               len(neighbors[a])) for a in range(len(x))]

    # To-do: compute LOFs when requested, not for all elements here
    lofs = [sum(lrds[u] for u in neighbors[a])/len(neighbors[a])
            for a in range(len(x))]

    return lambda u: lofs[u]


def local_outlier_2(x, k=1):
    '''Try some tweaks to see if it's faster.  UNTESTED.  TODO: Test.

    Jonathan already reduced some loops to comprehensions.  Try:
      0. Replace all 'len(x)' calls with local variable N
      1. Replacing 'distances' dictionary with an array.
      2. Pre-allocate 'neighbors' to avoid 'append' calls.
    '''
    N = len(x)
    # Can we set RN = range(N) and avoid repeated fn calls? Or are generators weird?
    distances = np.array(abs(x[b]-x[a] for a in range(N) for b in range(N)))

    neighbors = np.array((N,N))
    for a in range(N):
        y = [b for b in range(N) if b != a]
        y.sort(key=lambda b: distances[a, b])
        neighbors[a] = y

    k_distances = [distances[a, neighbors[a][k - 1]] for a in range(N)]
    reach_distances = [[(None if a == b else max(k_distances[b], distances[a, b])) for b in range(N)] for a in range(N)]
    lrds = [1/(sum(reach_distances[a][b] for b in neighbors[a])/len(neighbors[a])) for a in range(N)]
    lofs = [sum(lrds[u] for u in neighbors[a])/len(neighbors[a]) for a in range(N)]

    return lambda u: lofs[u]
