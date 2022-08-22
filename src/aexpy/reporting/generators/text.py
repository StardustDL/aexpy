from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import IO

from aexpy.models import (ApiDescription, ApiDifference,
                          Distribution, Release, Report)
from aexpy.models.difference import BreakingRank, DiffEntry

from . import GeneratorReporter, ProcessData, ReportGenerator

BCIcons = {
    BreakingRank.Compatible: "🟢",
    BreakingRank.Low: "🟡",
    BreakingRank.Medium: "🟠",
    BreakingRank.High: "🔴",
    BreakingRank.Unknown: "❔",
}

BCLevel = {
    BreakingRank.Compatible: "✅",
    BreakingRank.Low: "❓",
    BreakingRank.Medium: "❗",
    BreakingRank.High: "❌",
    BreakingRank.Unknown: "❔"
}

StageIcons = {
    "preprocess": "📦",
    "extract": "🔍",
    "diff": "📑",
    "evaluate": "🔬",
    "report": "📜"
}


def formatMessage(item: "DiffEntry") -> str:
    ret = []
    submessages = item.message.split(': ', 1)
    ret.append(" ".join([BCIcons[item.rank], submessages[0].strip()]))
    if len(submessages) > 1:
        for entry in submessages[1].split(";"):
            cur = entry.strip().removesuffix(".")
            cur = cur.replace("=>", " → ")
            ret.append("     " + cur)
    return "\n".join(ret)


class TextReportGenerator(ReportGenerator):
    """Generate a text report."""

    def generate(self, data: "ProcessData") -> str:
        result = ""

        distDuration: "timedelta" = data.oldDistribution.duration + \
            data.newDistribution.duration
        desDuration: "timedelta" = data.oldDescription.duration + data.newDescription.duration
        totalDuration: "timedelta" = distDuration + \
            desDuration + data.diff.duration

        level, changesCount = data.diff.evaluate()

        result += f"""📜 {data.oldRelease} → {data.newRelease} {BCLevel[level]}

▶ {data.oldRelease}
  📦 {data.oldDistribution.wheelFile}
  📁 {data.oldDistribution.wheelDir}
  🔖 {data.oldDistribution.pyversion}
  📚 {', '.join(data.oldDistribution.topModules)}
  💠 {len(data.oldDescription.entries)} entries

▶ {data.newRelease}
  📦 {data.newDistribution.wheelFile}
  📁 {data.newDistribution.wheelDir}
  🔖 {data.newDistribution.pyversion}
  📚 {', '.join(data.newDistribution.topModules)}
  💠 {len(data.newDescription.entries)} entries

⏰  Creation {datetime.now()}
⏱  Duration {totalDuration.total_seconds()}s
  {StageIcons["preprocess"]} Preprocessing ⏱ {distDuration.total_seconds()}s
    {data.oldDistribution.creation}
    {data.newDistribution.creation}
  {StageIcons["extract"]} Extracting ⏱ {desDuration.total_seconds()}s
    {data.oldDescription.creation}
    {data.newDescription.creation}
  {StageIcons["diff"]} Diffing ⏱ {data.diff.duration.total_seconds()}s
    {data.diff.creation}\n"""

        changes = data.diff.breaking(BreakingRank.Unknown)
        bcs = data.diff.breaking(BreakingRank.Low)
        nbcs = data.diff.rank(BreakingRank.Unknown) + \
            data.diff.rank(BreakingRank.Compatible)

        if len(changes) > 0:
            result += f"\n📋 Changes {' '.join([f'{BCIcons[rank]} {changesCount[rank]}' for rank in sorted(changesCount.keys(), reverse=True)])}\n"

        if len(bcs) > 0:
            result += "\n🚧 Breakings\n\n"
            bcs.sort(key=lambda x: (x.rank, x.kind), reverse=True)
            for item in bcs:
                result += f"{formatMessage(item)}\n"

        if len(nbcs) > 0:
            result += "\n🧪 Non-breakings\n\n"
            nbcs.sort(key=lambda x: (x.rank, x.kind), reverse=True)
            for item in nbcs:
                result += f"{formatMessage(item)}\n"

        result += "\n"
