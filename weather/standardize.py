#!/usr/bin/env python3
# SARbayes/standardize.py


import xlrd


workbook = xlrd.open_workbook('../ISRIDclean-updated.xlsx')
worksheet = workbook.sheet_by_index(0)

for index in range(1, worksheet.nrows):
    row = worksheet.row_values(index)
    date, lkp_ns, lkp_ew = row[3], row[33], row[34]
    if date and lkp_ns and lkp_ew:
        print(index, row[1], lkp_ns, lkp_ew)
        # print(index, row[1], row[4], row[5], lkp_ns, lkp_ew)
