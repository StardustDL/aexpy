from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from typing import IO

from aexpy.models import ApiDescription, Distribution, Release, ApiBreaking, ApiDifference, Report
from aexpy.models.difference import BreakingRank, DiffEntry

from . import ReportGenerator, ProcessData


BCIcons = {
    BreakingRank.Compatible: "🟢",
    BreakingRank.Low: "🟡",
    BreakingRank.Medium: "🟠",
    BreakingRank.High: "🔴",
}


def formatMessage(item: "DiffEntry") -> str:
    ret = []
    submessages = item.message.split(':', 1)
    ret.append(" ".join([BCIcons[item.rank], submessages[0].strip()]))
    if len(submessages) > 1:
        for entry in submessages[1].split("; "):
            cur = entry.strip().removesuffix(".")
            cur = cur.replace(":", ": ", 1)
            cur = cur.replace("->", " → ")
            ret.append("     " + cur)
    return "\n".join(ret)


class TextReportGenerator(ReportGenerator):
    def generate(self, data: "ProcessData", file: "IO[str]"):
        print("📜", data.oldRelease, data.newRelease, file=file)

        distDuration: "timedelta" = data.oldDistribution.duration + \
            data.newDistribution.duration
        desDuration: "timedelta" = data.oldDescription.duration + data.newDescription.duration
        totalDuration: "timedelta" = distDuration + \
            desDuration + data.diff.duration + data.bc.duration
        print("\n⏱️  Duration",
              totalDuration.total_seconds(), file=file)
        print(" ", "Preprocessing",
              distDuration.total_seconds(), file=file)
        print(" ", "Extracting",
              desDuration.total_seconds(), file=file)
        print(" ", "Differing",
              data.diff.duration.total_seconds(), file=file)
        print(" ", "Evaluating",
              data.bc.duration.total_seconds(), file=file)

        print("\n📝 Breaking Changes", end="", file=file)

        for item in reversed(BreakingRank):
            items = data.bc.rank(item)
            if items:
                print(" ", BCIcons[item], len(
                    items), end="", file=file)

        print("\n", file=file)

        changes = data.bc.breaking(BreakingRank.Low)
        changes.sort(key=lambda x: (x.rank, x.kind), reverse=True)
        for item in changes:
            print(formatMessage(item), file=file)
