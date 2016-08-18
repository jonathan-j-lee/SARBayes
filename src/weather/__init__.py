"""
weather -- Historical weather data API access

The purpose of this module is to provide a Python interface to online historic
weather data APIs. Each API is represented as a submodule.
"""

__all__ = ['noaa', 'wsi']

from weather import noaa, wsi
