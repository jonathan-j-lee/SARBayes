"""
server.server_lifecycle
"""

import os
import sys


def on_server_loaded(server_context):
    """
    Once the server is loaded, append the current working directory to the
    locations where Python searches for modules (the server is expected to run
    from `src`, which would allow the frontend to access the database).

    Arguments:
        server_context: Supplied by Bokeh.
    """
    cwd = os.getcwd()
    sys.path.append(cwd)  # Relative imports
