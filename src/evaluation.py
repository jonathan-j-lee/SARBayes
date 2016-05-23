"""
evaluation
==========
"""


class Result:
    ...


def brier_score(predictions, outcomes):
    if len(predictions) != len(outcomes):
        raise ValueError('prediction and outcome length mismatch')

    return sum(pow(prediction - outcome, 2) for prediction, outcome in
               zip(predictions, outcomes))/len(predictions)


def cross_validate(predictions, outcomes, folds=10):
    ...


def leave_one_out():
    ...
