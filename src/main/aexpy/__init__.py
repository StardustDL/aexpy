import logging
import os

import click

__version__ = "0.0.1"


def get_app_directory():
    return os.path.split(__file__)[0]
