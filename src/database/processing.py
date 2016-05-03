"""
database.processing
===================
"""

__all__ = ['survival_rate']

import numpy as np
import pandas as pd

from .models import Base, Subject


def survival_rate(subjects):
    subjects = subjects.filter(Subject.status != None)
    return subjects.filter(Subject.survived).count()/subjects.count()
