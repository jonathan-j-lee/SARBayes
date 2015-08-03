#!/usr/bin/env python3
# SARbayes/ISRID/formatting2.py


import datetime
import geopy
import openpyxl
import warnings
import weather
import yaml

warnings.filterwarnings('ignore')
datefmt = '%Y-%m-%d %H:%M:%S'

with open('settings.yaml') as settings_file:
    settings = yaml.load(settings_file)
    weather.API_TOKENS = settings['tokens'][1:]


workbook_filename, tab_filename = 'ISRID-2015-NY.xlsx', 'ISRID-NY2.tab'
workbook = openpyxl.load_workbook(workbook_filename, read_only=True)
worksheet = workbook.active
print('Worksheet title: "{}"'.format(worksheet.title))

with open(tab_filename, 'w+') as tab_file:
    """
    print('Key #', 'Status', 'Age', 'Sex', 'Category', 'HighTemp', 'LowTemp', 
        'WindSpeed', 'Snow', 'Rain', sep='\t', file=tab_file)
    print('string', 'discrete', 'continuous', 'discrete', 
        'discrete', 'continuous', 'continuous', 'continuous', 'continuous', 
        'continuous', sep='\t', file=tab_file)
    print('meta', 'class', '', '', '', '', '', '', '', '', 
        sep='\t', file=tab_file)
    """
    
    for index, row in enumerate(worksheet.rows):
        values = tuple(cell.value for cell in row)
        if index == 0:
            continue
        
        key, incident_datetime = values[1], values[4]
        city, county = values[9], values[10]
        category = values[20]
        age, sex, status = values[33], values[34], values[46]
        incident_duration = values[110]
        ipp = values[113]
        
        if key <= 452:
            continue
        
        if type(ipp) is str:
            lat, lon = ipp.split(', ')
            lat, lon = float(lat), float(lon)
        
        if type(incident_datetime) is not datetime.datetime:
            if ':' not in incident_datetime:
                incident_datetime += ' 00:00:00'
            incident_datetime = datetime.datetime.strptime(
                incident_datetime, datefmt)
        
        assert type(incident_datetime) is datetime.datetime
        conditions = None
        if lat and lon and incident_datetime:
            point = geopy.Point(lat, lon)
            conditions = weather.get_conditions(incident_datetime, point)
            print('({}, {}) @ "{}" -> {}'.format(lat, lon, 
                incident_datetime.isoformat(), conditions))
        
        key = str(key)
        if not status or 'N/A' in status.upper().strip():
            continue
        elif status.upper().strip() in ('SUSPENDED', 'DOA'):
            status = 'DEAD'
        elif 'N/A' not in status.upper().strip():
            status = 'ALIVE'
        
        age = str(age) if age else ''
        if sex is None:
            sex = ''
        else:
            assert sex.upper() in ('M', 'F')
            sex = sex.upper()
        
        if category:
            category = category.upper().strip()
        else:
            category = ''
        
        if not conditions:
            continue
        
        high_temp = str(round(conditions['TMAX']/10, 3)) \
            if conditions['TMAX'] is not None else ''
        low_temp = str(round(conditions['TMIN']/10, 3)) \
            if conditions['TMIN'] is not None else ''
        wind_speed = str(round(3.6*conditions['AWND'], 3)) \
            if conditions['AWND'] is not None else ''
        snow = str(round(conditions['SNOW'], 3)) \
            if conditions['SNOW'] is not None else ''
        rain = str(round(max(conditions['PRCP'] - (float(snow) 
            if type(snow) is str and snow else 0.0), 0.0), 3)) \
            if conditions['PRCP'] is not None else ''
        
        features = [
            key, 
            status, 
            age, 
            sex, 
            category, 
            high_temp, 
            low_temp, 
            wind_speed, 
            snow, 
            rain
        ]
        
        print('\t'.join(features), file=tab_file)
