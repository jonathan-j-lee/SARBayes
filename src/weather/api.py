"""
weather/api.py
"""

import json
import urllib.error
import urllib.parse
import urllib.request


def fetch_json(base_url: str, endpoint: str,
        parameters: dict={}, headers: dict={}):
    url = urllib.parse.urljoin(base_url, endpoint)
    url += '?' + urllib.parse.urlencode(parameters, safe=':,')
    request = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(request)
    return json.loads(response.read().decode('utf-8'))
