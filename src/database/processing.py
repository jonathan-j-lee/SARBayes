"""
database.processing
===================
"""

__all__ = ['survival_rate', 'tabulate', 'to_orange_table']

import numpy as np
import Orange
import pandas as pd

from .models import Subject


def survival_rate(subjects):
    subjects = subjects.filter(Subject.status != None)
    return subjects.filter(Subject.survived).count()/subjects.count()


def tabulate(query, not_null=True):
    columns = query.column_descriptions

    if not_null:
        criteria = map(lambda column: column['expr'] != None, columns)
        query = query.filter(*criteria)

    df = pd.read_sql(query.statement, query.session.bind)
    df.columns = list(map(lambda column: column['name'], columns))

    return df


def to_orange_table(df):
    ...
    # domain = Orange.data.Domain()
