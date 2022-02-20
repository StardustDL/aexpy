from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import IO

from aexpy.models import ApiDescription, Distribution, Release, ApiBreaking, ApiDifference, Report
from aexpy.models.difference import BreakingRank, DiffEntry

from . import GeneratorReporter, ReportGenerator, ProcessData


BCIcons = {
    BreakingRank.Compatible: "🟢",
    BreakingRank.Low: "🟡",
    BreakingRank.Medium: "🟠",
    BreakingRank.High: "🔴",
    BreakingRank.Unknown: "❔",
}


def formatMessage(item: "DiffEntry") -> str:
    ret = []
    submessages = item.message.split(': ', 1)
    ret.append(" ".join([BCIcons[item.rank], submessages[0].strip()]))
    if len(submessages) > 1:
        for entry in submessages[1].split(";"):
            cur = entry.strip().removesuffix(".")
            cur = cur.replace("->", " → ")
            ret.append("     " + cur)
    return "\n".join(ret)


class TextReportGenerator(ReportGenerator):
    """Generate a text report."""

    def generate(self, data: "ProcessData", file: "IO[str]"):
        distDuration: "timedelta" = data.oldDistribution.duration + \
            data.newDistribution.duration
        desDuration: "timedelta" = data.oldDescription.duration + data.newDescription.duration
        totalDuration: "timedelta" = distDuration + \
            desDuration + data.diff.duration + data.bc.duration
        
        changesCount = []

        level = None

        for item in reversed(BreakingRank):
            items = data.bc.rank(item)
            if items:
                if not level:
                    match item:
                        case BreakingRank.Compatible:
                            level = "✅"
                        case BreakingRank.Low:
                            level = "❓"
                        case BreakingRank.Medium:
                            level = "❗"
                        case BreakingRank.High:
                            level = "❌"
                changesCount.append((item, len(items)))
        
        changes = data.bc.breaking(BreakingRank.Low)

        level = level or "✅"

        print(f"""📜 {data.oldRelease} → {data.newRelease} {level}

▶ {data.oldRelease}
  📦 {data.oldDistribution.wheelFile}
  📁 {data.oldDistribution.wheelDir}
  🔖 {data.oldDistribution.pyversion}
  📚 {', '.join(data.oldDistribution.topModules)}

▶ {data.newRelease}
  📦 {data.newDistribution.wheelFile}
  📁 {data.newDistribution.wheelDir}
  🔖 {data.newDistribution.pyversion}
  📚 {', '.join(data.newDistribution.topModules)}

📝 Changes {' '.join([f"{BCIcons[rank]} {value}" for rank, value in changesCount])}

⏰  Creation {datetime.now()}
⏱  Duration {totalDuration.total_seconds()}s
  📦 Preprocessing ⏱ {distDuration.total_seconds()}s
    {data.oldDistribution.creation}
    {data.newDistribution.creation}
  🔍 Extracting ⏱ {desDuration.total_seconds()}s
    {data.oldDescription.creation}
    {data.newDescription.creation}
  📑 Differing ⏱ {data.diff.duration.total_seconds()}s
    {data.diff.creation}
  🔬 Evaluating ⏱ {data.bc.duration.total_seconds()}s
    {data.bc.creation}
""", file=file)

        if len(changes) > 0:
            print("🚧 Breakings\n", file=file)
            changes.sort(key=lambda x: (x.rank, x.kind), reverse=True)
            for item in changes:
                print(formatMessage(item), file=file)
        
        print("", file=file)
