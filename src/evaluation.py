"""
evaluation
==========
"""

import numpy as np
import pandas as pd


def compute_brier_score(predictions, outcomes):
    predictions, outcomes = np.asarray(predictions), np.asarray(outcomes)
    return np.sum(np.power(predictions - outcomes, 2))/len(predictions)


def cross_validate(df, fit, predict, folds=10, name='prediction'):
    if folds > len(df):
        raise ValueError('more folds than samples')

    test_size = int(np.ceil(len(df)/folds))
    predictions = pd.DataFrame(index=df.index, columns=[name])

    for fold, testing_cases in df.groupby(np.arange(len(df)) // test_size):
        training_cases = df[~df.index.isin(testing_cases.index)]
        assert len(testing_cases) + len(training_cases) == len(df)

        model = fit(training_cases)
        for index, testing_case in testing_cases.iterrows():
            predictions.set_value(index, name, predict(model, testing_case))

    return predictions
