"""
server.main

$ bokeh serve --show server
"""

from bokeh.models import Button, CheckboxButtonGroup, MultiSelect, Panel, Slider, Tabs, HBox, VBox
from bokeh.plotting import figure, curdoc, vplot
from collections import Counter
from functools import reduce

import database
from database.models import Incident, Group, Subject
from database.processing import tabulate


# Get data

engine, session = database.initialize('sqlite:///../data/isrid-master.db')

query = session.query(Subject.survived, Incident.total_hours, Group.category,
                      Group.size, Subject.age, Subject.sex_as_str)
query = query.join(Group, Incident)
df = tabulate(query)

database.terminate(engine, session)


# Build UI

plot = figure()

categories = Counter(df['category'])
categories = sorted(categories, key=lambda category: -categories[category])

category_select = MultiSelect(value=categories, options=categories,
                              title='Category')
size_select = Slider(start=1, end=max(df['size']), value=1, step=1,
                     title='Group Size')
age_min_select = Slider(start=0, end=max(df['age']), value=0, step=1,
                        title='Minimum Age')
age_max_select = Slider(start=0, end=max(df['age']), value=max(df['age']),
                        step=1, title='Maximum Age')
sex_select = CheckboxButtonGroup(labels=['Male', 'Female'], active=[0, 1])

selectors = Tabs(tabs=[
    Panel(child=HBox(category_select), title='Category'),
    Panel(child=HBox(size_select), title='Group Size'),
    Panel(child=HBox(age_min_select, age_max_select), title='Age'),
    Panel(child=sex_select, title='Sex')
])

def callback():
    """
    Dynamically generate a Kaplan-Meier plot.
    """
    """
    df_ = df[age_min_select.value <= df.age]
    df_ = df_[df_.age <= age_max_select.value]
    if 0 not in sex_select.active:
        df_ = df_[df_.sex_as_str != 'male']
    if 1 not in sex_select.active:
        df_ = df_
    """

callback()

generate = Button(label='Generate')
generate.on_click(callback)

document = curdoc()
document.add_root(vplot(plot, selectors, generate))
