import os
import sys


def on_server_loaded(server_context):
    cwd = os.getcwd()
    sys.path.append(cwd)  # Relative imports
