"""
server.main

$ bokeh serve --show server
"""

from bokeh.models import Button, CheckboxButtonGroup, MultiSelect, Panel, Slider, Tabs, HBox, VBox
from bokeh.plotting import figure, curdoc, vplot
from collections import Counter
from lifelines import KaplanMeierFitter

import database
from database.models import Incident, Group, Subject
from database.processing import tabulate


# Get data

engine, session = database.initialize('sqlite:///../data/isrid-master.db')

query = session.query(Subject.survived, Incident.total_hours, Group.category,
                      Group.size, Subject.age, Subject.sex)
query = query.join(Group, Incident)
df = tabulate(query)

database.terminate(engine, session)


# Build UI

plot = figure()

categories = Counter(df['category'])
categories = sorted(categories, key=lambda category: -categories[category])
category_select = MultiSelect(value=categories, options=categories,
                              title='Category')

min_size_select = Slider(start=1, end=max(df['size']), value=1, step=1,
                         title='Minimum Group Size')
max_size_select = Slider(start=1, end=max(df['size']), value=max(df['size']),
                         step=1, title='Maximum Group Size')

min_age_select = Slider(start=0, end=max(df['age']), value=0, step=1,
                        title='Minimum Age')
max_age_select = Slider(start=0, end=max(df['age']), value=max(df['age']),
                        step=1, title='Maximum Age')

sex_select = CheckboxButtonGroup(labels=['Male', 'Female'], active=[0, 1])

selectors = Tabs(tabs=[
    Panel(child=HBox(category_select), title='Category'),
    Panel(child=HBox(min_size_select, max_size_select), title='Group Size'),
    Panel(child=HBox(min_age_select, max_age_select), title='Age'),
    Panel(child=sex_select, title='Sex')
])

def callback():
    """
    Dynamically generate a Kaplan-Meier plot.
    """
    df_ = df.copy()

    print(category_select.value)
    for category in categories:
        if category not in category_select.value:
            df_ = df_[df_.category != category]

    df_ = df_[min_size_select.value <= df_['size']]
    df_ = df_[df_['size'] <= max_size_select.value]

    df_ = df_[min_age_select.value <= df_.age]
    df_ = df_[df_.age <= max_age_select.value]

    if 0 not in sex_select.active:
        df_ = df_[df_.sex != 1]
    if 1 not in sex_select.active:
        df_ = df_[df_.sex != 2]

    days = [total_hours.total_seconds()/3600/24
            for total_hours in df.total_hours]

    kmf = KaplanMeierFitter()
    #kmf.fit()

callback()

generate = Button(label='Generate')
generate.on_click(callback)

document = curdoc()
document.add_root(vplot(plot, selectors, generate))
