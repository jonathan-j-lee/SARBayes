#!/usr/bin/env python3
# SARbayes/weather/format.py

"""
SARbayes

This module standardizes coordinates as latitude and longitude format.

Notes: 
  * New Zealand uses its own coordinate systems, NZMG.
    See http://apps.linz.govt.nz/coordinate-conversion/index.aspx.
  * For township and range coordinates, the centroid coordinate was taken.
  * xlsxwriter can only create new spreadsheets, not modify existing ones.

More resources: 
  * https://www.google.com/maps
  * http://www.rcn.montana.edu/resources/converter.aspx
  * http://www.earthpoint.us/TownshipsSearchByDescription.aspx
"""

import xlrd
import xlsxwriter
import re

DECIMAL = r'^-{0,1}\d*\.\d+$'
DMS = r'^\d{1,3}[\s\.\'\"]\d{1,3}[\s\.\'\"]\d{1,3}$'


def process(row, index, datemode):
    lkp_ns, lkp_ew = str(row[33]).strip(), str(row[34]).strip()
    if lkp_ns and lkp_ew:
        m1, m2 = re.match(DECIMAL, lkp_ns), re.match(DECIMAL, lkp_ew)
        if m1 and m2:
            return
        m1, m2 = re.match(DMS, lkp_ns), re.match(DMS, lkp_ew)
        if m1 and m2:
            return
        
        # Ignore unreadable cases


def modify_database(
        input_filename, output_filename, sheet_name, processing_function):
    input_workbook = xlrd.open_workbook(input_filename)
    input_worksheet = input_workbook.sheet_by_name(sheet_name)
    
    output_workbook = xlsxwriter.Workbook(output_filename)
    output_worksheet = output_workbook.add_worksheet(sheet_name)
    
    output_worksheet.write_row('A1', input_worksheet.row_values(0))  # Header
    for index in range(1, input_worksheet.nrows):
        row = input_worksheet.row_values(index)
        processing_function(row, index, input_workbook.datemode)
        output_worksheet.write_row('A{}'.format(index + 1), row)
    
    output_workbook.close()


if __name__ == '__main__':
    modify_database(
        '../ISRID-1.xlsx', '../ISRID-2.xlsx', 'ISRIDclean', process)
