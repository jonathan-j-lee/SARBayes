"""
database.processing
===================
"""

__all__ = ['survival_rate', 'tabulate', 'export_orange']

from numbers import Real
import numpy as np
from Orange.data import ContinuousVariable, DiscreteVariable
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


def export_orange(df):
    variables = []

    for name in df:
        dtype = df[name].dtype
        if issubclass(df[name].dtype, Real):
            variable_type = ContinuousVariable
        else:
            variable_type = DiscreteVariable

        variables.append(variable_type(name))

    print(variables)
    # domain = Orange.data.Domain()
