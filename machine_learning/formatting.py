#!/usr/bin/env python3
# SARbayes/machine_learning/formatting.py


import openpyxl
import Orange
import yaml
import datetime


def main():
    with open('settings.yaml') as settings_file:
        settings = yaml.load(settings_file)
    
    with open('ISRID.tab', 'w+') as tab_file:
        workbook = openpyxl.load_workbook('ISRID-updated.xlsx')
        worksheet = workbook.active
        start = datetime.datetime(1900, 1, 1)  # Excel start date
        
        print('\t'.join(attribute.get('name', '') 
            for attribute in settings['columns']), file=tab_file)
        print('\t'.join(attribute['type'] 
            for attribute in settings.get('columns', '')), file=tab_file)
        print('\t'.join(attribute.get('flag', '') 
            for attribute in settings['columns']), file=tab_file)
        
        for index, row in enumerate(worksheet.rows):
            if index == 0:
                continue
            
            attributes = {attribute['name']: '' 
                for attribute in settings['columns']}
            for attribute in settings['columns']:
                try:
                    value = row[attribute['index']].value
                    
                    if value is None:
                        continue
                    elif type(value) is datetime.time:
                        value = value.hour + value.minute/60 + value.second/3600
                    elif type(value) is datetime.datetime:
                        value = (value - start).total_seconds()/3600
                        if value < 0:
                            raise ValueError
                    
                    if attribute['type'] == 'continuous':
                        value = float(value)
                    elif attribute['type'] == 'string':
                        value = str(value)
                    elif attribute['type'] == 'discrete':
                        value = str(value)
                        if attribute['name'] == 'sex':
                            value = value[0]
                        elif attribute['name'] == 'status':
                            value = (
                                'DEAD' if 'DOA' in value.upper() else 'ALIVE')
                    
                    attributes[attribute['name']] = value
                except (TypeError, ValueError):
                    pass
            
            if not attributes['status'] or sum(str(value) != '' 
                    for name, value in attributes.items() if name not in (
                    'key', 'status')) < 4:
                continue
            print('\t'.join(str(attributes[attribute['name']]) 
                for attribute in settings['columns']), file=tab_file)


if __name__ == '__main__':
    main()
