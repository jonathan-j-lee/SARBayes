"""
evaluation -- Models evaluation tools
"""

import numpy as np
import pandas as pd


def compute_brier_score(predictions, outcomes):
    """
    Compute the Brier score of a sequence of probabilistic forecasts and
    their associated outcomes. This scoring rule is given by

    $$BS = \frac{1}{N} \sum_{i=1}^N (f_i - o_i)^2$$

    where $f_i$ is the forecast of the $i$th case, $o_i$ is the observed
    outcome, and $N$ is the number of cases evaluated.

    Source: https://en.wikipedia.org/wiki/Brier_score

    Arguments:
        predictions: A sequence of probabilities (i.e. real numbers between
                     zero and one).
        outcomes: A sequence of observations (i.e. a zero for the event not
                  occurring, and a one otherwise). Each associated prediction
                  and outcome share an index.

    Returns:
        A real number between zero and one (inclusive) that is the Brier score
        (i.e. the mean of the square of every error term).
    """
    predictions, outcomes = np.asarray(predictions), np.asarray(outcomes)
    return np.sum(np.power(predictions - outcomes, 2))/len(predictions)


def cross_validate(df, fit, predict, folds=10, name='prediction'):
    """
    Evaluate a model with k-fold cross-validation:

        1. Divide the cases into k contiguous segments.
        2. Select an untested segment as the test cases.
        3. Use the other k - 1 segments to train a model.
        4. Generate predictions for the test cases.
        5. Go back to step 2 until there are forecasts for every observation.
        6. Return the forecasts.

    Arguments:
        df: A `pandas` dataframe, with each row representing a case.
        fit: A function that accepts a `pandas` dataframe containing the
             training data and returns a model. The model can be anything, as
             long as the `predict` function accepts it (see next argument).
        predict: A function that accepts the model and a test case (a `pandas`
                 series) and returns a probability.
        folds: The number of folds to use.
        name: The name of the column in the returned dataframe.

    Returns:
        A dataframe with one column labeled with the `name` argument containing
        the model's forecasts. The index of the result corresponds to that of
        the data passed in, `df`.
    """
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
