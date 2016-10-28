"""
database.processing -- Database processing tools
"""

__all__ = ['survival_rate', 'tabulate', 'export_to_orange']

import numpy as np
from Orange.data import ContinuousVariable, DiscreteVariable, Domain, Table
import pandas as pd

from database.models import Subject


def survival_rate(subjects):
    """
    Calculate the survival rate of a group of subjects.

    Arguments:
        subjects: An SQLAlchemy `Query` object of `Subject` instances.

    Returns:
        A float between zero and one, inclusive, representing the survival rate
        of the given subjects with a definite status.
    """
    subjects = subjects.filter(Subject.status != None)
    return subjects.filter(Subject.survived).count()/subjects.count()


def tabulate(query, not_null=True):
    """
    Convert an SQLAlchemy `Query` object into a `pandas` dataframe.

    Arguments:
        query: An `SQLAlchemy` query object.
        not_null: A list of booleans, one per column in the query. For each
                  column, if its corresponding value in `not_null` is `True`,
                  exclude all rows where that column's value is null.
                  Alternatively, a single boolean can be supplied, which is
                  applied to all columns.

    Returns:
        A `pandas` dataframe containing the rows in the query.

    Raises:
        ValueError: if `not_null` is a list and its size is not the same as the
                    number of columns in the query.
    """
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


def export_to_orange(df, *class_names,
                     from_duration=lambda delta: delta.total_seconds()/3600):
    """
    Convert a `pandas` dataframe to an Orange `Table`.

    Arguments:
        df: A `pandas` dataframe.
        class_names: The columns in the dataframe considered to be class
                     variables.
        from_duration: A one-argument function that converts a
                       `numpy.timedelta64` object into a number. By default,
                       the number of seconds is used.

    Returns:
        An appropriately configured Orange `Table` object containing the data
        in `df`.
    """
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
            value = df[name][index]
            table[index][name] = (value if isinstance(value, str)
                                  else value.item())

    return table
