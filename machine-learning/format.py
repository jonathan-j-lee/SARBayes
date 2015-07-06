#!/usr/bin/env python3
# SARbayes/machine-learning/format.py


import json
import xlrd


def process(attributes, row):
    row = list(row[attr['index']] for index in attributes)
    print(row)


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
    main('../ISRIDclean.xlsx', 'format.json', 'ISRID.tab')
