"""
database.processing
===================
"""

__all__ = ['survival_rate', 'tabulate', 'export_as_orange']

import numpy as np
from Orange.data import ContinuousVariable, DiscreteVariable, Domain, Table
import pandas as pd

from .models import Subject


def survival_rate(subjects):
    subjects = subjects.filter(Subject.status != None)
    return subjects.filter(Subject.survived).count()/subjects.count()


def tabulate(query, not_null=True):
    columns = query.column_descriptions

    if isinstance(not_null, bool):
        not_null = [not_null]*len(columns)
    elif len(not_null) != len(columns):
        raise ValueError('column length mismatch')

    criteria = [column['expr'] != None
                for column, to_filter in zip(columns, not_null) if to_filter]
    query = query.filter(*criteria)

    df = pd.read_sql(query.statement, query.session.bind)
    df.columns = list(map(lambda column: column['name'], columns))

    return df


def export_as_orange(df, *class_names,
                  from_duration=lambda delta: delta.total_seconds()/3600):
    features, classes = [], []

    for name, dtype in zip(df.columns, df.dtypes):
        if np.issubdtype(dtype, np.timedelta64):
            df[name] = list(map(from_duration, df[name]))

        if np.issubdtype(dtype, np.number):
            variable = ContinuousVariable(name)
        else:
            variable = DiscreteVariable(name, set(df[name]))

        if name in class_names:
            classes.append(variable)
        else:
            features.append(variable)

    domain = Domain(features, classes)
    table = Table.from_domain(domain, len(df))

    for index in range(len(df)):
        for name in df.columns:
            table[index][name] = df[name][index].item()

    return table
