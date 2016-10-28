#!/usr/bin/env python3

"""
kaplanmeier -- Survival analysis using the Kaplan-Meier estimator
"""

from collections import Counter
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from lifelines import KaplanMeierFitter

from evaluation import compute_brier_score, cross_validate
from util import read_simple_data


def plot_grid(fitters, rows=3, columns=3, size=(15, 10), max_days=30,
              title='Kaplan-Meier Survival Curves'):
    """
    Plot a grid of Kaplan-Meier curves.

    Arguments:
        fitters: A list of `KaplanMeierFitter` instances (must have at least
                 `rows` times `columns` elements).
        rows: The subplot grid's number of rows.
        columns: The subplot grid's number of columns.
        size: The size of the figure.
        max_days: The maximum number of days to display predictions for.
        title: The overall figure title.

    Returns:
        figure: A Matplotlib figure object containing the plot.
        axes: Matplotlib axes containing the individual subplots.
    """
    if len(fitters) < rows*columns:
        raise ValueError('fewer fitters than requested')

    figure, axes = plt.subplots(rows, columns, figsize=size)
    base_font_size = matplotlib.rcParams.get('font.size', 12)
    styles = censor_styles={'marker': '|', 'ms': base_font_size/2}

    for row in range(rows):
        for column in range(columns):
            ax, fitter = axes[row, column], fitters[row*columns + column]
            fitter.plot(show_censors=True, censor_styles=styles, ax=ax)

            ax.set_xlim(0, min(max_days, 1.05*ax.get_xlim()[1]))
            ax.set_ylim(0, 1)

            category, count = fitter._label, len(fitter.durations)
            ax.set_title('{} (N = {})'.format(category, count))
            ax.set_xlabel('Total Incident Time (days)')
            ax.set_ylabel('Probability of Survival')

            ax.legend_.remove()
            ax.grid(True)

    figure.suptitle(title, fontsize=1.5*base_font_size)
    figure.tight_layout()
    figure.subplots_adjust(top=0.9)

    return figure, axes


def plot_combined(fitters, size=(15, 10), max_days=15,
                  title='Kaplan-Meier Survival Curves', smooth=False):
    """
    Plot a list of Kaplan-Meier curves on one set of axes.

    Arguments:
        fitters: A list of `KaplanMeierFitter` instances.
        size: The size of the figure.
        max_days: The maximum number of days to display predictions for.
        title: The title of the figure.
        smooth: A boolean that, when `True`, overrides the default stepwise
                plot to generate a smooth curve.

    Returns:
        figure: A Matplotlib figure object containing the plot.
        ax: A Matplotlib ax object.
    """
    figure = plt.figure(figsize=size)
    ax = figure.add_subplot(1, 1, 1)

    base_font_size = matplotlib.rcParams.get('font.size', 12)
    styles = {'marker': '|', 'ms': base_font_size/2}

    for fitter in fitters:
        if smooth:
            fitter.survival_function_.plot(ax=ax)
        else:
            fitter.plot(show_censors=True, censor_styles=styles, ci_show=False,
                        ax=ax)

    ax.set_xlim(0, min(max_days, 1.05*ax.get_xlim()[1]))
    ax.set_ylim(0, 1)

    ax.set_title(title, fontsize=1.5*base_font_size)
    ax.set_xlabel('Total Incident Time (days)')
    ax.set_ylabel('Probability of Survival')

    ax.grid(True)

    return figure, ax


class NaiveSurvivalRateModel:
    """
    A model that guesses the probability of survival is always the overall
    survival rate.
    """
    def fit(self, times, doa, label=None):
        """
        Fit a survival rate model instance to data.

        Arguments:
            times: A sequence of incident times.
            doa: A sequence of booleans indicating whether the incident ended
                 with the subject dead-on-arrival (same length as `times`).
            label: A name to attach to the model instance.

        Returns:
            self: The model instance.
        """
        assert len(times) == len(doa)
        self.label, self.survival_rate = label, 1 - sum(doa)/len(doa)
        return self

    def predict(self, time):
        """
        Predict a subject's probability of survival with the survival rate.

        Arguments:
            time: The time the model should make a prediction for (unused).

        Returns:
            The prediction (in this case, the survival rate).
        """
        return self.survival_rate


def preprocess(df):
    """
    Preprocess the data by filtering out categories with too few cases.

    Arguments:
        df: The raw (unprocessed) data as a `pandas` dataframe.

    Returns:
        A `pandas` dataframe without categories with fewer than 20 cases or
        fewer than two deaths (this is to prevent models from obtaining perfect
        scores by overfitting).
    """
    excluded = []
    for category, df_subset in df.groupby('category'):
        if len(df_subset) < 20 or sum(df_subset.doa.as_matrix()) < 2:
            excluded.append(category)
    return df[~df.category.isin(excluded)]


def make_fitting_function(model, df_default=None, label=None):
    """
    Make a function that will fit a model on some training data.

    Arguments:
        model: The model to make a fitting function for (has a `fit` method).
        df_default: If not `None`, this overrides the training data.
        label: A label to attach to the model instance.

    Returns:
        fit: A one-argument function that takes in training data as a `pandas`
             dataframe containing `days` and `doa` columns, and returns a
             fitted model instance (depends on the model's implementation).
    """
    def fit(training_cases):
        instance = model()
        df = training_cases if df_default is None else df_default
        return instance.fit(df.days, df.doa, label=label)
    return fit


def evaluate_fit(df, fit_fn, predict_fn, repeat=10):
    """
    Evaluate a model instance (fitter) with cross-validation.

    Arguments:
        df: A `pandas` dataframe containing the cases to test the model on.
            These cases are shuffled between cross-validation runs.
        fit_fn: A one-argument function that takes in training data as a
                `pandas` dataframe and returns a fitted model (see
                `evaluation.cross_validate`).
        predict_fn: A two-argument function that takes in the fitted model
                    instance and a test case and returns a prediction.
        repeat: The number of times to repeat cross-validation.

    Returns:
        score: The mean Brier score for the category between cross-validation
               runs.
        errors: A list of all signed error values measured (across cross-
                validation runs).
    """
    subscores, errors = [], []
    for iteration in range(repeat):
        df = df.sample(n=len(df))

        forecast = cross_validate(df, fit_fn, predict_fn)
        predictions = [forecast.ix[index].prediction for index in df.index]
        outcomes = df.survived.as_matrix().astype(int)

        subscores.append(compute_brier_score(predictions, outcomes))
        errors += list(forecast.prediction - outcomes)
    return np.mean(subscores), errors


def main():
    """
    Fit Kaplan-Meier curves to each category and evaluate the performance of
    the curves against a naive survival rate model.
    """
    url = 'sqlite:///../data/isrid-master.db'
    df_singles = read_simple_data(url, exclude_groups=True)
    df_singles = preprocess(df_singles)

    categories, counts = zip(*Counter(df_singles.category).most_common())
    survival_rates = []
    naive_scores, km_scores = [], []
    naive_errors, km_errors = [], []

    naive_fit = make_fitting_function(NaiveSurvivalRateModel)
    predict = lambda model, test_case: model.predict(test_case.days)
    km_fit_fns = []

    for category in categories:
        df_subset = df_singles[df_singles.category == category]
        survival_rates.append(sum(df_subset.survived)/len(df_subset))

        km_fit = make_fitting_function(KaplanMeierFitter, df_subset, category)
        km_fit_fns.append(km_fit)

        score, errors = evaluate_fit(df_subset, naive_fit, predict)
        naive_scores.append(score)
        naive_errors += errors

        score, errors = evaluate_fit(df_subset, km_fit, predict)
        km_scores.append(score)
        km_errors += errors

    ## Statistics

    avg_abs_naive_error = np.abs(naive_errors).mean()
    print('Average absolute naive error: {:.3f}'.format(avg_abs_naive_error))
    avg_abs_km_error = np.abs(km_errors).mean()
    print('Average absolute KM error: {:.3f}'.format(avg_abs_km_error))

    error_diffs = [abs(naive_error) - abs(km_error)
                   for naive_error, km_error in zip(naive_errors, km_errors)]
    null_bound = 0.05

    print('Proportions: ')
    print('  Increase in error: {:.3f}%'.format(sum(diff < -null_bound
          for diff in error_diffs)/len(error_diffs)*100))
    print('  No significant change: {:.3f}%'.format(sum(-null_bound <= diff
          <= null_bound for diff in error_diffs)/len(error_diffs)*100))
    print('  Decrease in error: {:.3f}%'.format(sum(null_bound < diff
          for diff in error_diffs)/len(error_diffs)*100))

    ## Kaplan-Meier Plots

    km_fitters = [km_fit(None) for km_fit in km_fit_fns]

    figure, axes = plot_grid(km_fitters[:9])
    figure.savefig('../doc/figures/kaplan-meier/grid.svg', transparent=True)

    old_font_size = matplotlib.rcParams['font.size']
    matplotlib.rc('font', size=20)
    figure, axes = plot_grid(km_fitters[:4], rows=2, columns=2)
    figure.savefig('../doc/figures/kaplan-meier/grid-large.svg',
                   transparent=True)
    matplotlib.rc('font', size=old_font_size)

    figure, axes = plot_combined(km_fitters[:4])
    figure.savefig('../doc/figures/kaplan-meier/combined.svg',
                   transparent=True)

    ## Absolute Error Difference Histogram

    plt.figure(figsize=(10, 8))
    plt.title('Distribution of Differences in Absolute Error ($N = {}$)'
              .format(len(df_singles)))
    plt.xlabel('Difference in Absolute Error ($\Delta E$)')
    plt.ylabel('Frequency')
    plt.hist(error_diffs, 200, [-1, 1], weights=[0.1]*len(error_diffs),
             alpha=0.6)

    greatest_frequency = plt.ylim()[1]
    plt.plot([-null_bound]*2, [0, greatest_frequency], 'r--', alpha=0.6)
    plt.plot([null_bound]*2, [0, greatest_frequency], 'r--', alpha=0.6)
    plt.plot([0, 0], [0, greatest_frequency], 'b--', alpha=0.6)
    plt.ylim(0, greatest_frequency)
    plt.tight_layout()
    plt.savefig('../doc/figures/evaluation/abs-error-diff-dist.svg',
                transparent=True)

    ## Brier Score Boxplot

    plt.figure(figsize=(10, 8))
    plt.title('Brier Scores Across Categories')
    plt.ylabel('Brier Score')
    plt.boxplot([naive_scores, km_scores], vert=True,
                labels=['Survival Rate', 'Kaplan-Meier'])

    colormap = plt.get_cmap('RdYlGn')
    f = lambda r: (r - min(survival_rates))/(1 - min(survival_rates))
    c = list(map(colormap, map(f, survival_rates)))

    x = np.random.normal(1, 0.025, size=len(categories))
    plt.scatter(x, naive_scores, s=counts, alpha=0.3, c=c)
    plt.scatter(x + 1, km_scores, s=counts, alpha=0.3, c=c)
    plt.ylim(0, 0.25)
    plt.tight_layout()
    plt.savefig('../doc/figures/evaluation/brier-score-boxplot.svg',
                transparent=True)

    ## Brier Score Scatterplot

    plt.figure(figsize=(10, 10))
    plt.title('Brier Score Comparison')
    plt.xlabel('Brier Score with Kaplan-Meier')
    plt.ylabel('Brier Score with Survival Rate')
    plt.scatter(km_scores, naive_scores, counts, c=c, alpha=0.3)

    t = np.linspace(0, 0.25, 100)
    plt.plot(t, t, 'b--')
    plt.xlim(0, 0.25)
    plt.ylim(0, 0.25)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('../doc/figures/evaluation/brier-score-comparison.svg',
                transparent=True)

    plt.show()

    # TODO: logrank tests between categories


if __name__ == '__main__':
    main()
