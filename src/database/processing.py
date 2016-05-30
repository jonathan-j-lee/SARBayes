"""
database.processing
===================
"""

__all__ = ['survival_rate', 'tabulate']

import numpy as np
import pandas as pd
import re

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


def standardize_category(category, merge=True):
    category = category.strip().casefold()

    if merge:
        for keyword in 'child', 'skier', 'vehicle':
            pattern = r'\b({})\b'.format(keyword)
            result = re.search(pattern, category)
            if result:
                return result.group(1)

    return category
