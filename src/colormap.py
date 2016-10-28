#!/usr/bin/env python3

"""
colormap -- Visualize survival rates for different categories and age groups

This standalone script takes subjects from the 10 most common categories, bins
subjects within each group by age (in increments of 10 years, up to 100 years),
and calculates the survival rate within each bin. Then, each bin is plotted as
a square on a grid and colored by the survival rate (greener for greater
survival, redder for lesser survival).
"""

import matplotlib.pyplot as plt
import numpy as np

import database
from database.models import Subject, Group
from database.processing import tabulate


def main():
    """
    Plot the profile (size and survival rate) of the most common categories.
    """
    ## Read data

    engine, session = database.initialize('sqlite:///../data/isrid-master.db')

    query = session.query(Subject.age, Group.category, Subject.survived)
    query = query.join(Group)
    df = tabulate(query)

    database.terminate(engine, session)

    ## Process subjects by category and age

    selected_categories = df.category.value_counts()[:10].index.tolist()
    df = df[df.category.isin(selected_categories)]
    age_bins = np.linspace(0, 100, 11)

    survival_rates = np.full((10, 10), np.nan, dtype=np.float64)
    subgroup_sizes = np.full((10, 10), 0, dtype=np.float64)
    min_subgroup_size = 10

    for category, group in df.groupby('category'):
        group.insert(len(group.columns), 'age_bin',
                     np.digitize(group.age, age_bins))

        for age_index, subgroup in group.groupby('age_bin'):
            survivals = subgroup.survived.values.tolist()
            key = age_index - 1, selected_categories.index(category)

            if len(survivals) > min_subgroup_size:
                survival_rates[key] = sum(survivals)/len(survivals)
                subgroup_sizes[key] = len(survivals)

                # Debugging
                lower, upper = age_bins[age_index - 1], age_bins[age_index]
                print('{}, {} - {} years old'.format(category, int(lower),
                      int(upper)))
                print('  Survival rate: {:.3f}%'.format(
                      100*survival_rates[key]))
                print('  Number of subjects: {}'.format(
                      int(subgroup_sizes[key])))

    ## Plot survival rates and subgroup sizes

    canvas = plt.matshow(survival_rates, fignum=False, cmap='RdYlGn',
                         origin='lower')
    colorbar = plt.colorbar(canvas)
    colorbar.solids.set_edgecolor('face')
    colorbar.set_label('Survival Rate')

    x_positions = y_positions = np.arange(0, 10)
    for x in x_positions:
        for y in y_positions:
            plt.text(x, y, int(subgroup_sizes[y, x]) or '',
                     horizontalalignment='center', verticalalignment='center')

    plt.title('Lost Person Category Profiles')
    plt.ylabel('Age (years)')
    plt.xlabel('Category')

    ax = plt.gca()
    ax.xaxis.tick_bottom()
    plt.yticks(np.linspace(0, 10, 11) - 0.5, age_bins.astype(np.int))
    plt.xticks(x_positions, selected_categories, rotation=60)
    plt.subplots_adjust(bottom=0.2)
    plt.tight_layout()
    plt.savefig('../doc/figures/subject-data/category-profiles.svg',
                transparent=True)
    plt.show()


if __name__ == '__main__':
    main()
