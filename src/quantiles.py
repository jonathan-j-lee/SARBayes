"""
Empirical Quantile Curves
"""

import matplotlib.pyplot as plt
from scipy.stats.mstats import mquantiles

import database
from database.models import Subject, Group, Incident


engine, session = database.initialize('sqlite:///../data/isrid-master.db')

columns = Subject.survived, Group.category, Incident.total_hours
criteria = map(lambda column: column != None, columns)
query = session.query(*columns).join(Group, Incident).filter(*criteria)

database.terminate(engine, session)


from sqlalchemy import func
query = query.filter(Subject.survived == True,
                     func.upper(Group.category) == 'HIKER')
times = [total_hours.total_seconds()/3600/24
         for survived, category, total_hours in query]
print(mquantiles(times, [0.25, 0.5, 0.75, 0.95]))

"""
# Old code

categories = {}
for survived, category, total_hours in query:
    category = category.strip().upper()
    total_hours = total_hours.total_seconds()/3600

    if category not in categories:
        categories[category] = []

    categories[category].append((total_hours, survived))

figure, axes = plt.subplots(3, 3, figsize=(15, 11))
sequence = sorted(categories, key=lambda category: -len(categories[category]))

for index, category in zip(range(9), sequence):
    data = categories[category]
    hours = [total_hours for total_hours, survived in data]

    quantiles = list(mquantiles(hours, [0.25, 0.5, 0.75, 0.95, 0.997]))
    quantiles = [0] + quantiles + [float('inf')]
    print(category, quantiles)

    times, probabilities, counts = [], [], []

    for lowerbound, upperbound in zip(quantiles[:-1], quantiles[1:]):
        survivals = [survived for lost_hours, survived in data
                     if lowerbound <= lost_hours < upperbound]

        if len(survivals) > 0:
            times.append(lowerbound)
            probabilities.append(sum(survivals)/len(survivals))
            counts.append(len(survivals))

    ax = axes[index//3, index%3]
    ax.plot(times, probabilities)
    ax.set_title('{}, N = {}'.format(category, sum(counts)))
    ax.set_xlabel('Total Incident Time (h)')
    ax.set_ylabel('Probability of Survival')
    ax.set_xlim(0, 1.05*max(times))
    ax.set_ylim(0, 1)

figure.suptitle('Empirical Quantile Curves by Category', fontsize=20)
figure.tight_layout()
plt.subplots_adjust(top=0.925)
plt.show()
"""
