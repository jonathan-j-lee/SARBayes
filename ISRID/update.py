#!/usr/bin/env python3
# SARbayes/ISRID/update.py

"""
SARbayes

Database cleaning routine (improved).
"""


import argparse
import formatting
import openpyxl
import util
import warnings
import yaml


def update_row(index, input_row, column_settings, output_worksheet, styles):
    row_values = list(input_cell.value for input_cell in input_row)
    if index > 0:
        formatting.standardize(index, row_values, column_settings)
    
    for value in row_values:
        output_cell = openpyxl.writer.dump_worksheet.WriteOnlyCell(
            output_worksheet, value)
        for attribute, style in styles.items():
            setattr(output_cell, attribute, style)
        else:
            yield output_cell


def update_database(input_filename, output_filename, settings_filename):
    util.log('Updating database ... ')
    
    util.log('Reading settings file ... ')
    with open(settings_filename) as settings_file:
        settings = yaml.load(settings_file)
        style_settings = settings.get('styles', dict())
        column_settings = settings.get('columns', dict())
        title, styles = settings.get('title', 'ISRID'), dict()
        
        util.log('Creating styles ... ')
        for attribute, arguments in style_settings.items():
            if attribute == 'font':
                style = openpyxl.styles.Font(**arguments)
            else:
                style = None
            styles[attribute] = style
    
    util.log('Reading input (optimized) ... ')
    input_workbook = openpyxl.load_workbook(input_filename, read_only=True)
    input_worksheet = input_workbook.active
    
    util.log('Creating output workbook ... ')
    output_workbook = openpyxl.Workbook(write_only=True, optimized_write=True)
    output_worksheet = output_workbook.create_sheet(title=title)
    
    util.log('Writing output (optimized) ... ')
    for index, input_row in enumerate(input_worksheet.rows):
        output_row = update_row(
            index, input_row, column_settings, output_worksheet, styles)
        output_worksheet.append(output_row)
    else:
        output_workbook.save(output_filename)
        util.log('Done.')


def main():
    try:
        parser = argparse.ArgumentParser(description='Update ISRID.')
        parser.add_argument('input_filename', 
            help='Filename of the input spreadsheet.')
        parser.add_argument('output_filename', 
            help='Filename of the output spreadsheet.')
        parser.add_argument('settings_filename', 
            help='Filename of the settings (in YAML format).')
        
        args = parser.parse_args()
        warnings.filterwarnings('ignore')
        update_database(**vars(args))
    except KeyboardInterrupt:
        quit(1)


if __name__ == '__main__':
    main()
