#!/usr/bin/env python3

"""
kaplanmeier
===========
Survival analysis
"""

from collections import Counter
import matplotlib
import matplotlib.pyplot as plt
from lifelines import KaplanMeierFitter

from evaluation import compute_brier_score
from util import read_simple_data


def evaluate_fitters(df, fitters):
    for fitter in fitters:
        df_subset = df[df.category == fitter._label]

        predictions = list(map(fitter.predict, df_subset.days))
        outcomes = df_subset.survived
        base_survival_rate = sum(df_subset.survived)/len(df_subset)

        prediction_score = compute_brier_score(predictions, outcomes)
        base_score = compute_brier_score([base_survival_rate]*len(df_subset),
                                         outcomes)

        yield base_score, prediction_score


def fit_data(df):
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
    df_groups = read_simple_data(url, exclude_singles=True)

    fitters = list(fit_data(df_singles))

    fitters = [fitter for fitter in fitters if len(fitter.durations) > 10]

    brier_scores = evaluate_fitters(df_singles, fitters)
    base_scores, prediction_scores = zip(*brier_scores)

    plt.title('Brier Scores Across Categories')
    plt.ylabel('Brier Score')

    plt.boxplot([base_scores, prediction_scores], vert=True,
                labels=['Survival Rate', 'Kaplan-Meier'])

    plt.savefig('../doc/figures/brier-score-boxplot.svg', transparent=True)
    plt.show()

    # title = 'Kaplan-Meier Survival Curves of Most Common Categories'
    # figure, axes = plot_grid(fitters, 3, 3, title=title)
    # figure, axes = plot_combined(fitters[:6])
    # matplotlib.rc('font', size=20)
    # plt.show()

    # To-do: logrank tests


if __name__ == '__main__':
    execute()
