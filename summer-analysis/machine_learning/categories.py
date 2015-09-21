#!/usr/bin/env python3
# SARbayes/machine_learning/categories.py

import openpyxl

wb = openpyxl.load_workbook('../ISRID/ISRID-survival.xlsx', read_only=True)
ws = wb.active

k = {}

for index, row in enumerate(ws.rows):
    values = [cell.value for cell in row]
    if index == 0:
        continue
    category, status = values[5], values[10]
    if category is None or status is None:
        continue
    status = status.split(',')
    status = int(all(_.upper().strip() not in ('SUSPENDED', 'DOA') 
        for _ in status))
    category = category.upper().strip()
    
    # Begin rules
    if '=FALSE()' in category:
        continue
    if 'YOUTH' in category:
        category = 'YOUTH'
    if 'SKIER' in category or 'SKI' in category:
        category = 'SKIER'
    if 'CHILD' in category:
        category = 'CHILD'
    if 'DEMENTIA' in category:
        category = 'DEMENTIA'
    if 'WATER' in category:
        category = 'WATER'
    
    if category not in k:
        k[category] = [0, 0]
    k[category][1] += 1
    k[category][0] += status

for category, _ in k.items():
    if _[1] < 20:
        continue
    print(category, _[0]/_[1], _[1])
