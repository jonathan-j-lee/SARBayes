#!/usr/bin/env python3
# SARbayes/machine_learning/group-size.py

import openpyxl

wb = openpyxl.load_workbook('../ISRID/ISRID-survival.xlsx', read_only=True)
ws = wb.active

numbers = {}

for index, row in enumerate(ws.rows):
    values = [cell.value for cell in row]
    if index == 0:
        continue
    status = values[10]
    if status is None:
        continue
    status = status.split(',')
    if len(status) not in numbers:
        numbers[len(status)] = [0, 0]
    numbers[len(status)][1] += 1
    numbers[len(status)][0] += int(any(_.upper().strip() in (
        'SUSPENDED', 'DOA') for _ in status))

_x, _y, _w = [], [], []
for key in sorted(numbers):
    value = numbers[key]
    x = key
    y = 1.0 - value[0]/value[1]
    print(x, y)
    _x.append(x)
    _y.append(y)
    _w.append(value[1])

import numpy as np

m, b = fit = np.polyfit(_x, _y, 1, w=_w)
print(m, b)
fit = np.poly1d(fit)

import matplotlib.pyplot as plt

plt.scatter(_x, _y, s=_w)
plt.plot(_x, fit(_x))
plt.show()
