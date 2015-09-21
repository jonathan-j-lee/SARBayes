#!/usr/bin/env python3
# SARbayes/ISRID/nps-update.py

import weather
import yaml
import openpyxl
import warnings

warnings.filterwarnings('ignore')

with open('settings.yaml') as settings_file:
    settings = yaml.load(settings_file)
    weather.API_TOKENS = settings['tokens']

wbin = openpyxl.load_workbook('combined NPS Data (SEKI and ZION).xlsx', read_only=True)
for ws in wbin:
    for index, row in enumerate(ws.rows):
        values = [cell.value for cell in row]
        if index == 0:
            continue
        
        if ws.title != 'SEKI NPS Data':
            datetime, location, ipp = values[4], values[8], values[113]
        else:
            continue
        
        if ipp:
            lat, lon = ipp.split(' , ')
            if ' ' in lat:
                comps = lat.strip().split(' ')
                lat = sum(float(j)/pow(60, i) for i, j in enumerate(comps))
            if ' ' in lon:
                comps = lon.strip().split(' ')
                lon = sum(float(j)/pow(60, i) for i, j in enumerate(comps))
            lat, lon = float(lat), float(lon)
        else:
            print(location)
