from datetime import timedelta
import sys
from aexpy.models.difference import BreakingRank, DiffEntry
from ..models import Distribution, Release, ApiDescription, ApiDifference, ApiBreaking, Report
from . import Reporter as Base
from ..utils import TeeFile, ensureDirectory


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


def reportTxt(oldRelease: "Release", newRelease: "Release",
              oldDistribution: "Distribution", newDistribution: "Distribution",
              oldDescription: "ApiDescription", newDescription: "ApiDescription",
              diff: "ApiDifference",
              bc: "ApiBreaking",
              file):
    print("📜", oldRelease, newRelease, file=file)

    distDuration: "timedelta" = oldDistribution.duration + newDistribution.duration
    desDuration: "timedelta" = oldDescription.duration + newDescription.duration
    totalDuration: "timedelta" = distDuration + \
        desDuration + diff.duration + bc.duration
    print("\n⏱️  Duration",
          totalDuration.total_seconds(), file=file)
    print(" ", "Preprocessing",
          distDuration.total_seconds(), file=file)
    print(" ", "Extracting",
          desDuration.total_seconds(), file=file)
    print(" ", "Differing",
          diff.duration.total_seconds(), file=file)
    print(" ", "Evaluating",
          bc.duration.total_seconds(), file=file)

    print("\n📝 Breaking Changes", end="", file=file)

    for item in reversed(BreakingRank):
        items = bc.rank(item)
        if items:
            print(" ", BCIcons[item], len(
                items), end="", file=file)

    print("\n", file=file)

    changes = bc.breaking(BreakingRank.Low)
    changes.sort(key=lambda x: (x.rank, x.kind), reverse=True)
    for item in changes:
        print(formatMessage(item), file=file)


class Reporter(Base):
    def report(self,
               oldRelease: "Release", newRelease: "Release",
               oldDistribution: "Distribution", newDistribution: "Distribution",
               oldDescription: "ApiDescription", newDescription: "ApiDescription",
               diff: "ApiDifference",
               bc: "ApiBreaking") -> "Report":
        assert oldDistribution.release == oldRelease, f"{oldDistribution.release} != {oldRelease}"
        assert newDistribution.release == newRelease, f"{newDistribution.release} != {newRelease}"
        assert oldDescription.distribution.release == oldRelease, f"{oldDescription.distribution.release} != {oldRelease}"
        assert newDescription.distribution.release == newRelease, f"{newDescription.distribution.release} != {newRelease}"
        assert diff.old.release == oldRelease, f"{diff.old.release} != {oldRelease}"
        assert diff.new.release == newRelease, f"{diff.new.release} != {newRelease}"
        assert bc.old.release == oldRelease, f"{bc.old.release} != {oldRelease}"
        assert bc.new.release == newRelease, f"{bc.new.release} != {newRelease}"

        cacheFile = self.cache / "results" / oldRelease.project / \
            f"{oldRelease}&{newRelease}.json"
        outFile = self.cache / "reports" / oldRelease.project / \
            f"{oldRelease}&{newRelease}.txt"

        with Report(old=oldRelease, new=newRelease, file=outFile).produce(cacheFile, self.logger, redo=self.redo) as ret:
            if ret.creation is None or not ret.file.exists():
                ensureDirectory(ret.file.parent)
                with ret.file.open("w") as out:
                    file = TeeFile(out, sys.stdout)
                    reportTxt(oldRelease, newRelease, oldDistribution, newDistribution,
                              oldDescription, newDescription, diff, bc, file)
            else:
                print(ret.file.read_text())

        return ret
