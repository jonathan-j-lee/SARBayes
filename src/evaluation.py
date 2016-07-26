"""
evaluation
==========
"""

import numpy as np


def compute_brier_score(predictions, outcomes):
    predictions, outcomes = np.asarray(predictions), np.asarray(outcomes)
    return np.sum(np.power(predictions - outcomes, 2))/len(predictions)
