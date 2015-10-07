#!/usr/bin/env python3
# SARbayes/src/migrate.py

"""
migrate.py -- ISRID Migration Script

Usage: 
 1. Create a YAML schema file for every workbook source.
 2. For every schema file, include an object, with each attribute name 
    corresponding to a worksheet title.
 3. For every worksheet title, include a list of column names, which should be 
    formatted as strings.
 4. Include the paths of the source and schema filenames in the "main" function.
"""


import datetime
import database
import openpyxl
import os
import sqlite3
import warnings
import yaml


def read_excel(filename, skip=1):
    workbook = openpyxl.load_workbook(filename, read_only=True)
    for worksheet in workbook:
        rows = (tuple(cell.value for cell in row) 
            for index, row in enumerate(worksheet.rows) if index >= skip)
        yield worksheet.title, rows


def initialize_db(db_filename, script_filename):
    initialized = os.path.exists(db_filename)
    connection = sqlite3.connect(db_filename, 
        detect_types=sqlite3.PARSE_DECLTYPES)
    
    if not initialized:
        with open(script_filename) as script_file:
            script = script_file.read()
        cursor = connection.cursor()
        cursor.executescript(script)
    return connection


def populate_db(connection, source_filenames, schema_filenames):
    cursor = connection.cursor()
    master_schema = database.schema.fetch_schema(cursor)
    filenames = zip(source_filenames, schema_filenames)
    
    try:
        for source_filename, schema_filename in filenames:
            with open(schema_filename) as schema_file:
                schema = yaml.load(schema_file.read())
            
            for title, rows in read_excel(source_filename):
                column_names = tuple(name for name in schema[title])
                for row in rows:
                    pass
                
                connection.commit()
    
    except Exception as e:
        print(e)


def terminate_db(connection):
    try:
        connection.commit()
    finally:
        connection.close()


def main():
    # Modify these filenames as necessary
    db_filename, script_filename = '../data/ISRID.sqlite', 'initialize.sql'
    source_filenames = (
        '../data/sources/ISRIDclean.xlsx', 
    )
    schema_filenames = (
        '../data/schemata/ISRID-clean.yaml', 
    )
    
    warnings.filterwarnings('ignore')
    connection = initialize_db(db_filename, script_filename)
    populate_db(connection, source_filenames, schema_filenames)
    terminate_db(connection)


if __name__ == '__main__':
    main()
