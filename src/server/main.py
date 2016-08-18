"""
server.main -- Kaplan-Meier curve frontend

To run, navigate to `src` and execute

    $ bokeh serve --show server

Bokeh will then redirect you to a webpage with a plot, four tabs (one each for
subsetting the cases by category, age, group size, and sex), and a generate
button.

When you click the generate button, Bokeh will call `generate_plot`, where the
data will be resliced and used to update the curve without a page refresh.
"""

from bokeh.models import (Button, CheckboxGroup, Panel, Paragraph, Slider,
                          Tabs, HBox)
from bokeh.models.ranges import Range1d
from bokeh.plotting import figure, curdoc, vplot
from collections import Counter
from lifelines import KaplanMeierFitter
import pandas as pd

import database
from database.models import Incident, Group, Subject
from database.processing import tabulate


# Get data

engine, session = database.initialize('sqlite:///../data/isrid-master.db')

query = session.query(Subject.survived, Incident.total_hours, Group.category,
                      Group.size, Subject.age, Subject.sex)
query = query.join(Group, Incident)
df = tabulate(query)
df['days'] = [hours.total_seconds()/3600/24 for hours in df.total_hours]

database.terminate(engine, session)


# Build UI

plot = figure(y_range=Range1d(bounds='auto', start=0, end=1 + 1e-3),
              plot_width=1000, title='Lost Person Survival Over Time')

status = Paragraph()  # Used for notifying the user when the constraints
                      # exclude all cases, rather than failing silently.

# Create a list of checkboxes for enabling each category
# Categories are sorted from largest to smallest
categories = Counter(df['category'])
categories = sorted(categories, key=lambda category: -categories[category])
category_select = CheckboxGroup(labels=categories, active=[0])

# Create sliders for constraining cases by minimum and maximum group sizes
# A double-ended slider would do better here, not sure if Bokeh has one
min_size_select = Slider(start=1, end=max(df['size']), value=1, step=1,
                         title='Minimum Group Size (Inclusive)')
max_size_select = Slider(start=1, end=max(df['size']), value=max(df['size']),
                         step=1, title='Maximum Group Size (Inclusive)')

# Similarly, create sliders for constraining cases by minimum and maximum ages
min_age_select = Slider(start=0, end=max(df['age']), value=0, step=1,
                        title='Minimum Age (Inclusive)')
max_age_select = Slider(start=0, end=max(df['age']), value=max(df['age']),
                        step=1, title='Maximum Age (Inclusive)')

# Create checkboxes for enabling each sex
sex_select = CheckboxGroup(labels=['Male', 'Female'], active=[0, 1])

# Combine all the widgets above into a tabbed pane
selectors = Tabs(tabs=[
    Panel(child=HBox(category_select), title='Category'),
    Panel(child=HBox(min_size_select, max_size_select), title='Group Size'),
    Panel(child=HBox(min_age_select, max_age_select), title='Age'),
    Panel(child=HBox(sex_select), title='Sex')
])

generate = Button(label='Generate')
renderer = plot.line([], [], line_width=2, line_alpha=0.75)


def generate_plot():  # Perhaps `regenerate_plot`?
    """ Dynamically fit and plot a Kaplan-Meier curve. """
    df_ = df.copy()

    # Use constraints
    for index in range(len(categories)):
        if index not in category_select.active:
            df_ = df_[df_.category != category_select.labels[index]]

    df_ = df_[min_size_select.value <= df_['size']]
    df_ = df_[df_['size'] <= max_size_select.value]

    df_ = df_[min_age_select.value <= df_.age]
    df_ = df_[df_.age <= max_age_select.value]

    if 0 not in sex_select.active:  # Male
        df_ = df_[df_.sex != 1]
    if 1 not in sex_select.active:  # Female
        df_ = df_[df_.sex != 2]

    if len(df_) == 0:  # Bad constraints
        status.text = 'No cases found. Try different constraints.'
        return

    doa = [not survived for survived in df_.survived]

    kmf = KaplanMeierFitter()
    fit = kmf.fit(df_.days, event_observed=doa, label='prob_of_surv')

    # Here, we are using the smoothed version of the Kaplan-Meier curve
    # The stepwise version would work just as well

    data, surv_func = renderer.data_source.data, fit.survival_function_
    data.update(x=surv_func.index, y=surv_func.prob_of_surv)

    start, end = 0, max(df_.days)
    # bounds='auto' doesn't work?
    plot.x_range.update(start=start, end=end, bounds=(start, end))
    status.text = '{} cases found.'.format(len(df_))


plot.xaxis.axis_label = 'Time (days)'
plot.yaxis.axis_label = 'Probability of Survival'

generate.on_click(generate_plot)
generate_plot()  # Start with Hikers, both sexes, all ages and group sizes

document = curdoc()
document.add_root(vplot(plot, status, generate, selectors))
