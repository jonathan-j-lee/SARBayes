#!/usr/bin/env python3
# SARbayes/weather/update.py

"""
SARbayes

This module adds missing weather data to the database.

See "help(weather)" for more information.
"""

import datetime
import geopy
import xlrd

from formatting import modify_database
import weather


def process(row, index, datemode):
    if index < 30198:
        return
    
    if row[3] and row[33] and row[34]:
        try:
            date = datetime.datetime(*xlrd.xldate_as_tuple(row[3], datemode))
        except (TypeError, xlrd.xldate.XLDateNegative):
            return
        
        try:
            lat, lon = float(row[33]), float(row[34])
            assert -90 <= lat < 90 and -180 <= lon <= 180
            coordinates = geopy.Point(lat, lon)
        except (ValueError, AssertionError):
            return
        
        old_weather_data = row[37:40] + row[41:43]
        if any(type(_) is str and len(_) == 0 for _ in old_weather_data):
            print('Updating case {} ... '.format(index + 1))
            try:
                conditions = weather.get_conditions(date, coordinates)
            except:
                print('ERROR')
                return
            
            if row[37] == '':
                if conditions['TMAX']:
                    row[37] = conditions['TMAX'] / 10
                    print('  High Temperature = {:.3f} degrees C'.format(row[37]))
            else:
                row[37] = round(float(row[37]), 3)
            
            if row[38] == '':
                if conditions['TMIN']:
                    row[38] = conditions['TMIN'] / 10
                    print('  Low Temperature = {:.3f} degrees C'.format(row[38]))
            else:
                row[38] = round(float(row[38]), 3)
            
            if row[39] == '':
                if conditions['AWND']:
                    row[39] = conditions['AWND'] * 3.6
                    print('  AVG Wind Speed = {:.3f} km/h'.format(row[39]))
            else:
                row[39] = round(float(row[39]), 3)
            
            if row[41] == '':
                if conditions['SNOW']:
                    row[41] = 'Yes' if conditions['SNOW'] > 0 else 'No'
                    print('  Snow = "{}"'.format(row[41]))
            
            if row[42] == '' and row[41] != '':
                if conditions['PRCP']:
                    row[42] = ('Yes' 
                        if row[41] == 'No' and conditions['PRCP'] > 0 else 'No')
                    print('  Rain = "{}"'.format(row[42]))


if __name__ == '__main__':
    modify_database(
        '../ISRID-4.xlsx', '../ISRID-5.xlsx', 'ISRIDclean', process)
