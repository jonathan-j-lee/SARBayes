"""
database.processing
===================
"""

from .models import Subject


def survival_rate(subjects):
    survivals = subjects.filter(Subject.survived == True)
    return survivals.count()/subjects.count()
