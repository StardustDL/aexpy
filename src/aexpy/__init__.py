from datetime import datetime
from functools import cache
import logging
import os
import pathlib

__version__ = "0.3.8"


LOGGING_FORMAT = "%(levelname)s %(asctime)s %(name)s [%(pathname)s:%(lineno)d:%(funcName)s]\n%(message)s\n"
LOGGING_DATEFMT = "%Y-%m-%d,%H:%M:%S"


def initializeLogging(level: int = logging.WARNING):
    root = logging.getLogger()
    root.setLevel(logging.NOTSET)
    root.handlers.clear()
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOGGING_FORMAT, LOGGING_DATEFMT))
    root.addHandler(handler)


def getAppDirectory():
    return pathlib.Path(__file__).parent.resolve()


def getCacheDirectory():
    return getAppDirectory() / "cache"


def getWorkingDirectory():
    return pathlib.Path(os.getcwd()).resolve()


def getCommitId():
    return os.getenv("GIT_COMMIT", "unknown")


def getBuildDate():
    try:
        return datetime.fromisoformat(os.getenv("BUILD_DATE", "unknown"))
    except:
        return datetime.now()


def runInDocker():
    return os.getenv("RUN_IN_DOCKER") is not None


CANDIDATE_ENV_MANAGER = ["micromamba", "mamba", "conda"]


@cache
def getEnvironmentManager():
    env = os.getenv("AEXPY_ENV_PROVIDER")
    if env in CANDIDATE_ENV_MANAGER:
        return env
    # auto detect
    import subprocess

    for env in CANDIDATE_ENV_MANAGER:
        try:
            subprocess.run(f"{env} --version", check=True, shell=True, timeout=5)
            return env
        except Exception:
            pass
    return "micromamba"
