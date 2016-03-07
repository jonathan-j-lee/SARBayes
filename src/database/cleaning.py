"""
database.cleansing
==================
"""

__all__ = ['extract_number']

import re

NUMBER = re.compile(r'(\-?\d*\.?\d+)')


def extract_number(text):
    result = NUMBER.search(text)
    if result:
        return float(result.group(1))
