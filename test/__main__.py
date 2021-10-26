import pytest
import pathlib
import sys

if __name__ == "__main__":
    if "redo" in sys.argv:
        from aexpy.env import env
        env.redo = True

    pytest.main([str(pathlib.Path(__file__).parent)])