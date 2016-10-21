"""
database.cleaning -- Data cleaning tools
"""

__all__ = ['extract_numbers']

import datetime
import re

NUMBER = re.compile(r'(\-?\d*\.?\d+)')


def extract_numbers(text):
    """
    Find all real numbers in a string.

    Arguments:
        text: A string to be searched.

    Returns:
        A generator of containing each number as a float, in the order in which
        they were found.

    >>> list(extract_numbers('no numbers'))
    []
    >>> list(extract_numbers('Outcome: 5 subjects, 2 DOA'))
    [5.0, 2.0]
    >>> list(extract_numbers('Between -.3 and 20.1 degrees Celsius'))
    [-0.3, 20.1]
    """
    yield from map(float, NUMBER.findall(text))


def coerce_type(value, datatype):
    """
    Naively attempt to coerce a value to a type.

    Arguments:
        value: The raw value to operate on (any type).
        datatype: The type the value should be.

    Returns:
        An equivalent value as type `datatype` if a conversion is possible, or
        `None` otherwise.
    """
    if isinstance(value, datatype) or value is None:
        return value

    elif datatype == str:
        return str(value)

    elif datatype in (int, float):
        try:
            return datatype(value)
        except (TypeError, ValueError):
            pass

        if isinstance(value, str):
            numbers = tuple(extract_numbers(value))

            if len(numbers) > 1:
                raise ValueError('more than one number found')
            elif len(numbers) == 1:
                return datatype(numbers[0])

        elif isinstance(value, datetime.timedelta):
            return datatype(value.total_seconds()/3600)

    elif datatype == datetime.timedelta:
        if isinstance(value, (int, float)):
            return datetime.timedelta(hours=24*value)

        elif isinstance(value, datetime.time):
            return datetime.timedelta(hours=value.hour, minutes=value.minute,
                                      seconds=value.second)

        elif isinstance(value, datetime.datetime):
            return value - EXCEL_START_DATE
