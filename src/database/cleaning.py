"""
database.cleaning
=================
"""

__all__ = ['extract_numbers']

import re

NUMBER = re.compile(r'(\-?\d*\.?\d+)')


def extract_numbers(text):
    yield from map(float, NUMBER.findall(text))
