#!/usr/bin/env python3

"""
database -- An SQLite 3 extension

Includes support for: 
  * cleaning, 
  * merging, 
  * validation, 
  * and reading schema.

Warning: 
  Currently, no protection is provided against SQL injection. This package is 
  only intended for personal use. Do not use in production.
"""


from . import schema
