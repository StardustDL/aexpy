from datetime import datetime
import json
import subprocess
import os
import sys
from pathlib import Path
import logging
import time
import traceback

LOGGING_FORMAT = "%(levelname)s %(asctime)s %(name)s [%(pathname)s:%(lineno)d:%(funcName)s]\n%(message)s\n"
LOGGING_DATEFMT = "%Y-%m-%d,%H:%M:%S"

logPath = Path(".") / "logs" / "ci.log"
logFile = None

scheduleHour = 1
CYCLE_SECOND = 1


def log(s: str):
    ts = f"{datetime.now()}: {s}"
    print(ts)
    print(ts, file=logFile)


def onCommit():
    subprocess.check_call("python -u exps/ci/onCommit.py".split())


def onSchedule():
    subprocess.check_call("python -u exps/ci/onSchedule.py".split())


def getCommitId():
    subprocess.check_call("git pull".split())
    return subprocess.check_output("git rev-parse HEAD".split(), text=True).strip()


def eventloop():
    lastCommit = getCommitId()
    scheduleDay = -1
    while True:
        cycle = CYCLE_SECOND
        try:
            config = json.loads(Path("exps/ci/ci.json").read_text())
            cycle = config["cycle"]
        except Exception as ex:
            cycle = CYCLE_SECOND
            log(f"Cycle reading exception: {'. '.join(traceback.format_exception(ex))}")
        time.sleep(cycle)

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
    if not logPath.parent.exists():
        os.makedirs(logPath.parent)
    with logPath.open("w") as log:
        logFile = log
        eventloop()


if __name__ == "__main__":
    main()
