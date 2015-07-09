#!/usr/bin/env python3
# SARbayes/weather/formatting.py

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

import coordinates
import xlrd
import xlsxwriter
import re

DECIMAL = r'^-{0,1}\d*\.\d+$'
DMS = r'^\d{1,3}[\s\.]\d{1,3}[\s\.]\d{1,3}$'


def process(row, index, datemode):
    lkp_ns, lkp_ew = str(row[33]).strip(), str(row[34]).strip()
    if lkp_ns and lkp_ew:
        m1, m2 = re.match(DECIMAL, lkp_ns), re.match(DECIMAL, lkp_ew)
        if m1 and m2:
            ns, ew = float(lkp_ns), float(lkp_ew)
            
            # Already latitude and longitude
            if -90 <= ns <= 90 and -180 <= ew <= 180 and \
                    ns % 1.0 != 0 and ew % 1.0 != 0:
                row[33], row[34] = round(ns, 6), round(ew, 6)
            # Truncated UTM
            elif 0 <= ns < 1000 and 0 <= ew < 1000:
                assert ns == int(ns) and ew == int(ew)
                ns, ew = str(int(ns)).rjust(3, '0'), str(int(ew)).rjust(3, '0')
                ns, ew = ns.ljust(5, '0'), ns.ljust(5, '0')
                if 'NY' in row[1]:
                    k = int(row[5])
                    ns = int('4' + str(k) + ns)
                    ew = int('5' + ew)
                    lat, lon = coordinates.utm_to_lat_lon(ew, ns, 18, 1)
                    row[33], row[34] = round(lat, 6), round(lon, 6)
            # UTM
            else:
                if 'NY' in row[1]:
                    lat, lon = coordinates.utm_to_lat_lon(ew, ns, 18, 1)
                    row[33], row[34] = round(lat, 6), round(lon, 6)
            
            return
        
        m1, m2 = re.match(DMS, lkp_ns), re.match(DMS, lkp_ew)
        if m1 and m2:
            lkp_ns, lkp_ew = lkp_ns.replace('.', ' '), lkp_ew.replace('.', ' ')
            dms_ns, dms_ew = lkp_ns.split(' '), lkp_ew.split(' ')
            s_ns, s_ew = dms_ns[2], dms_ew[2]
            if len(s_ns) > 2:
                dms_ns[2] = s_ns[:2] + '.' + s_ns[2:]
            if len(s_ew) > 2:
                dms_ew[2] = s_ew[:2] + '.' + s_ew[2:]
            
            ns = round(coordinates.dms_to_decimal(
                float(dms_ns[0]), float(dms_ns[1]), float(dms_ns[2])), 6)
            ew = round(coordinates.dms_to_decimal(
                float(dms_ew[0]), float(dms_ew[1]), float(dms_ew[2])), 6)
            
            row[33], row[34] = ns, ew
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
