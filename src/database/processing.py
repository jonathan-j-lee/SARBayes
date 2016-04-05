"""
database.processing
===================
"""

def survival_rate(subjects):
    return sum(subject.survived for subject in subjects)/subjects.count()
