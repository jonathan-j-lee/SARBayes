"""
database.processing
===================
"""

__all__ = ['survival_rate', 'as_array']

import numpy as np
import pandas as pd

from .models import Subject


def survival_rate(subjects):
    subjects = subjects.filter(Subject.status != None)
    return subjects.filter(Subject.survived).count()/subjects.count()


def as_array(column, filters=None, transform=None):
    dtype = np.dtype(column.type.python_type)
    query = column.parent.class_.query

    if filters is not None:
        query = filters(query)

    results = (instance for instance, *_ in query.from_self(column))
    if transform is not None:
        results = map(transform, results)

    return np.fromiter(results, dtype)


def as_dataframe(*columns):
    ...
