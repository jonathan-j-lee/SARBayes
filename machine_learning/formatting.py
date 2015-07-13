#!/usr/bin/env python3
# SARbayes/machine_learning/formatting.py


import itertools
import json
import xlrd


def process(attributes, row):
    data = list()
    
    for attr in attributes:
        item = row[attr['index']]
        if attr['name'] == 'status':
            item = 'DEAD' if 'DOA' in item else 'ALIVE'
        if type(item) is str and len(item) > 0:
            item = item.replace('.', ',').split(',')
            if attr['type'] == 'c':
                item = [float(_.replace('s', '')) 
                    for _ in item if _ and _ != '?']
        else:
            item = [item]
        data.append(item)
    
    for item in itertools.zip_longest(*data, fillvalue=None):
        item = list(item)
        while None in item:
            index = item.index(None)
            item[index] = str(data[index][0])
        item = list((str(_) if _ else '?') for _ in item)
        yield item


def main(input_filename, config_filename, output_filename):
    workbook = xlrd.open_workbook(input_filename)
    worksheet = workbook.sheet_by_index(0)
    
    with open(config_filename, 'r') as config_file:
        attributes = json.load(config_file)
    
    with open(output_filename, 'w+') as output_file:
        print('\t'.join(attr['name'] for attr in attributes), file=output_file)
        print('\t'.join(attr['type'] for attr in attributes), file=output_file)
        print('\t'.join(attr['meta'] for attr in attributes), file=output_file)
        
        for index in range(1, worksheet.nrows):
            row = worksheet.row_values(index)
            for data in process(attributes, row):
                print('\t'.join(data), file=output_file)


if __name__ == '__main__':
    main('../ISRID-updated.xlsx', 'format.json', 'ISRID.tab')
