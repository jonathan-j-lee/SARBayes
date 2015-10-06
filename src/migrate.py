#!/usr/bin/env python3

"""
migrate.py
"""


import datetime
import database
import os
import sqlite3
import yaml


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
    
    pass


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
    
    connection = initialize_db(db_filename, script_filename)
    populate_db(connection, source_filenames, schema_filenames)
    terminate_db(connection)


if __name__ == '__main__':
    main()
