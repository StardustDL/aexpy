from datetime import datetime
import subprocess
import os
import sys
from pathlib import Path
import logging
import time
import traceback

LOGGING_FORMAT = "%(levelname)s %(asctime)s %(name)s [%(pathname)s:%(lineno)d:%(funcName)s]\n%(message)s\n"
LOGGING_DATEFMT = "%Y-%m-%d,%H:%M:%S"

logPath = Path(".") / "ci.log"
logFile = None

scheduleHour = 1
CYCLE_SECOND = 1


def log(s: str):
    ts = f"{datetime.now()}: {s}"
    print(ts)
    print(ts, file=logFile)


def onCommit():
    log("New commit detected.")
    subprocess.check_call("cb build:docker".split())
    subprocess.check_call("cb serve:docker".split())


def onSchedule():
    log("Schedule task.")
    subprocess.check_call("cb data:clean".split())
    subprocess.check_call("cb -c docker=aexpy/aexpy -c provider=default -c project=click data:work".split())


def getCommitId():
    subprocess.check_call("git pull".split())
    return subprocess.check_output("git rev-parse HEAD".split(), text=True).strip()


def eventloop():
    lastCommit = getCommitId()
    scheduleDay = -1
    while True:
        time.sleep(CYCLE_SECOND)
        try:
            currentCommit = getCommitId()
            if currentCommit != lastCommit:
                log(f"New commit {currentCommit} from {lastCommit}.")
                onCommit()
                lastCommit = currentCommit
            now = datetime.now()
            if now.hour == scheduleHour and scheduleDay != now.day:
                print(f"Schedule at day {now.day}.")
                onSchedule()
                scheduleDay = now.day
        except Exception as ex:
            log(f"Exception: {'. '.join(traceback.format_exception(ex))}")


def main():
    global logFile
    with logPath.open("w") as log:
        logFile = log
        eventloop()


if __name__ == "__main__":
    main()
