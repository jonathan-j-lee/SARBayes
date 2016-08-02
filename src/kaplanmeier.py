#!/usr/bin/env python3

"""
kaplanmeier
===========
Survival analysis
"""

from collections import Counter
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from lifelines import KaplanMeierFitter

from evaluation import compute_brier_score, cross_validate
from util import read_simple_data


def evaluate_curves(df, fitters):
    for fitter in fitters:
        df_subset = df[df.category == fitter._label]

        predictions = list(map(fitter.predict, df_subset.days))
        outcomes = df_subset.survived
        base_survival_rate = sum(df_subset.survived)/len(df_subset)

        prediction_score = compute_brier_score(predictions, outcomes)
        base_score = compute_brier_score([base_survival_rate]*len(df_subset),
                                         outcomes)

        yield base_score, prediction_score


def fit_curves(df):
    categories = Counter(df.category)

    for category, count in categories.most_common():
        df_subset, fitter = df[df.category == category], KaplanMeierFitter()
        fitter.fit(df_subset.days, df_subset.doa, label=category)
        yield fitter


def plot_grid(fitters, rows=3, columns=3, size=(15, 10), max_days=30,
              title='Kaplan-Meier Survival Curves'):
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


def execute():
    url = 'sqlite:///../data/isrid-master.db'
    df_singles = read_simple_data(url, exclude_groups=True)

    excluded = []
    for category, df_subset in df_singles.groupby('category'):
        if len(df_subset) < 20 or sum(df_subset.doa.as_matrix()) < 2:
            excluded.append(category)

    df_singles = df_singles[~df_singles.category.isin(excluded)]

    # fitters = list(fit_curves(df_singles))
    categories = Counter(df_singles.category)
    categories, counts = zip(*categories.most_common())
    rates = []

    base_scores, prediction_scores = [], []
    for category in categories:
        df_subset = df_singles[df_singles.category == category]

        naive_fit = (lambda training_cases:
                     sum(training_cases.survived)/len(training_cases))
        naive_predict = lambda model, testing_case: model

        km_fit = (lambda training_cases: KaplanMeierFitter().fit(
                  df_subset.days, df_subset.doa, label=category))
        km_predict = lambda model, testing_case: model.predict(
                        testing_case.days)

        naive_predictions = cross_validate(df_subset, naive_fit, naive_predict)
        km_predictions = cross_validate(df_subset, km_fit, km_predict)

        outcomes = df_subset.survived.as_matrix().astype(int)
        naive_score = compute_brier_score([naive_predictions.ix[index].prediction for index in df_subset.index], outcomes)
        km_score = compute_brier_score([km_predictions.ix[index].prediction for index in df_subset.index], outcomes)

        base_scores.append(naive_score)
        prediction_scores.append(km_score)
        rates.append(sum(df_subset.survived)/len(df_subset))

    # brier_scores = evaluate_curves(df_singles, fitters)
    # base_scores, prediction_scores = zip(*brier_scores)

    # Brier Score Boxplot

    plt.title('Brier Scores Across Categories')
    plt.ylabel('Brier Score')

    plt.boxplot([base_scores, prediction_scores], vert=True,
                labels=['Survival Rate', 'Kaplan-Meier'])

    colormap = plt.get_cmap('RdYlGn')
    N = counts # [len(fitter.durations) for fitter in fitters]
    r = rates  #[1 - sum(fitter.event_observed)/len(fitter.event_observed)
        # for fitter in fitters]
    c = [colormap((rate - min(r))/(1 - min(r))) for rate in r]

    plt.scatter(np.random.normal(1, 0.025, size=len(base_scores)), base_scores,
                s=N, alpha=0.3, c=c)

    plt.scatter(np.random.normal(2, 0.025, size=len(prediction_scores)),
                prediction_scores, s=N, alpha=0.3, c=c)

    plt.ylim(0, 0.25)

    plt.savefig('../doc/figures/brier-score-boxplot.svg', transparent=True)

    # Brier Score Scatterplot

    figure = plt.figure(figsize=(10, 10))
    ax = figure.add_subplot(1, 1, 1)

    print('{:<32} {:<32} {:<32} {:<32}'.format('Category', 'Base Score', 'Prediction Score', 'Net Change'))
    print(' '.join('-'*32 for i in range(4)))
    for prediction_score, base_score, category in zip(prediction_scores, base_scores, categories):
        print('{:<32} {:<32.5f} {:<32.5f} {:<32.5f}'.format(category, base_score, prediction_score, prediction_score - base_score))

    ax.scatter(prediction_scores, base_scores, N, alpha=0.3)
    t = np.linspace(0, 0.25, 100)
    ax.plot(t, t, 'r--')

    ax.set_xlim(0, 0.25)
    ax.set_ylim(0, 0.25)

    ax.set_title('Brier Score Comparison')
    ax.set_xlabel('Brier Score by Kaplan-Meier')
    ax.set_ylabel('Brier Score by Survival Rate')
    ax.grid(True)

    figure.savefig('../doc/figures/brier-score-comparison.svg', transparent=True)

    plt.show()

    # title = 'Kaplan-Meier Survival Curves of Most Common Categories'
    # figure, axes = plot_grid(fitters, 3, 3, title=title)
    # figure, axes = plot_combined(fitters[:6])
    # matplotlib.rc('font', size=20)
    # plt.show()

    # To-do: logrank tests


if __name__ == '__main__':
    execute()
