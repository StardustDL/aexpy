import sys
import pathlib
import pytest
from tempfile import TemporaryDirectory


sys.path.append(
    str(pathlib.Path(__file__).parent.parent.joinpath("src").joinpath("main")))


def setup_module():
    print("SETUP...")

    from aexpy.env import env

    env.setPath(pathlib.Path(__file__).parent.joinpath("tempcache"))
    env.dev = True
    # env.redo = True


def teardown_module():
    print("TEARDOWN...")
