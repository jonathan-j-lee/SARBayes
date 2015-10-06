#!/usr/bin/env python3

"""
database/schema.py -- Python interface to SQLite schemata
"""


import sqlite3


class Table:
    def __init__(self, datatype, name, table_name, rootpage, sql):
        self.datatype, self.name, self.table_name = datatype, name, table_name
        self.rootpage, self.sql = rootpage, sql


class Column:
    def __init__(self, column_id, name, datatype, not_null, dflt_value, pk):
        self.column_id, self.name, self.datatype = column_id, name, datatype
        self.not_null, self.dflt_value, self.pk = not_null, dflt_value, pk


def fetch_table(cursor):
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    for attributes in cursor.fetchall():
        yield Table(*attributes)


def fetch_columns(cursor, table_name):
    cursor.execute('PRAGMA table_info({})'.format(table_name))
    for attributes in cursor.fetchall():
        yield Column(*attributes)
