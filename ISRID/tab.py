#!/usr/bin/env python3
# SARbayes/ISRID/tab.py

# 7fcca3999afe7cd9aab12f60d337fa78


import datetime
import openpyxl
import re

DECIMAL = re.compile(r'(\d+)')
START = datetime.datetime(1900, 1, 1)


with open('ISRID-survival.tab', 'w+') as tab_file:
    workbook = openpyxl.load_workbook('ISRID-survival.xlsx', read_only=True)
    worksheet = workbook.active
    worksheet.max_row = 81707
    
    def binify(status):
        if status:
            status = status.strip().upper()
            if 'DOA' in status or 'SUSPENDED' in status or 'DEAD' in status:
                return 'DEAD'
            elif status:
                return 'ALIVE'
    
    print('\t'.join([
        'status', 
        #'category', 
        #'sex', 
        #'age', 
        'hours', 
        #'temp_high', 
        #'temp_low', 
        #'wind_speed', 
        #'snow', 
        #'rain', 
        'hdd', 
        'cdd'
    ]), file=tab_file)
    
    print('\t'.join([
        'discrete', 
        #'discrete', 
        #'discrete', 
        #'continuous', 
        'continuous', 
        #'continuous', 
        #'continuous', 
        #'continuous', 
        #'continuous', 
        #'continuous', 
        'continuous', 
        'continuous'
    ]), file=tab_file)
    
    print('\t'.join([
        'class', 
        #'', 
        #'', 
        #'', 
        '', 
        #'', 
        #'', 
        #'', 
        #'', 
        #'', 
        '', 
        ''
    ]), file=tab_file)
    
    temp_base = 18
    doa, count = 0, 0
    for index, row in enumerate(worksheet.rows):
        if index == 0:
            continue
        
        data_source = row[0].value
        key = row[1].value
        incident_datetime = row[2].value
        city = row[3].value
        county = row[4].value
        category = row[5].value
        age = row[6].value
        sex = row[7].value
        weight = row[8].value
        height = row[9].value
        status = row[10].value
        incident_duration = row[11].value
        latitude = row[12].value
        longitude = row[13].value
        temp_max = row[14].value
        temp_min = row[15].value
        wind_speed = row[16].value
        snow = row[17].value
        rain = row[18].value
        
        status = binify(status)
        if status:
            if type(sex) is str:
                sex = sex[0].upper()
                if sex not in ('M', 'F'):
                    sex = ''
            else:
                sex = ''
            
            if type(age) in (float, int):
                age = str(int(age))
            elif type(age) is str:
                age = DECIMAL.search(age)
                if age:
                    age = age.group(0)
            if not age:
                age = ''
            
            if type(incident_duration) in (float, int):
                incident_duration = str(round(float(incident_duration), 3))
            elif type(incident_duration) is datetime.datetime:
                incident_duration = (incident_duration - START).total_seconds()/3600
                incident_duration /= 24
                incident_duration = str(round(float(incident_duration), 3)) \
                    if incident_duration > 0 else ''
            elif type(incident_duration) is datetime.time:
                incident_duration = incident_duration.hour + \
                    incident_duration.minute/60 + incident_duration.second/3600
                incident_duration /= 24
                incident_duration = str(round(float(incident_duration), 3)) \
                    if incident_duration > 0 else ''
            else:
                incident_duration = ''
            
            temp_max = str(round(temp_max, 3)) if type(temp_max) in (int, float) else ''
            temp_min = str(round(temp_min, 3)) if type(temp_min) in (int, float) else ''
            wind_speed = str(round(wind_speed, 3)) if type(wind_speed) in (int, float) else ''
            snow = str(round(snow, 3)) if type(snow) in (int, float) else ''
            rain = str(round(rain, 3)) if type(rain) in (int, float) else ''
            
            if type(row[14].value) in (int, float) and type(row[15].value) in (int, float):
                temp_avg = (row[14].value + row[15].value) / 2
                hdd = temp_base - temp_avg
                cdd = temp_avg - temp_base
                hdd = str(round(hdd, 3)) if hdd >= 0 else ''
                cdd = str(round(cdd, 3)) if cdd >= 0 else ''
            else:
                hdd, cdd = '', ''
            
            category = category.strip().upper() if type(category) is str else ''
            if category:
                pass
                #print(category)
            
            values = (
                status, 
                #category, 
                #sex, 
                #age, 
                incident_duration, 
                #temp_max, 
                #temp_min, 
                #wind_speed, 
                #snow, 
                #rain, 
                hdd, 
                cdd
            )
            
            if sum(1 for value in values if value) - 1 >= 2:
            # if sum(1 for value in values[3:] if value) >= 3:
                print('\t'.join(values), file=tab_file)
                if values[0] == 'DEAD':
                    doa += 1
                count += 1
    else:
        print('Survival rate: {:.3f}%'.format(100*(1 - doa/count)))
        print('Count:', count)
