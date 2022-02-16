from datetime import timedelta
import sys
from aexpy.models.difference import BreakingRank, DiffEntry
from ..models import Distribution, Release, ApiDescription, ApiDifference, ApiBreaking, Report
from . import Reporter as Base
from ..utils import TeeFile


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


class Reporter(Base):
    def report(self,
               oldRelease: "Release", newRelease: "Release",
               oldDistribution: "Distribution", newDistribution: "Distribution",
               oldDescription: "ApiDescription", newDescription: "ApiDescription",
               diff: "ApiDifference",
               bc: "ApiBreaking") -> "Report":
        assert oldDistribution.release == oldRelease
        assert newDistribution.release == newRelease
        assert oldDescription.distribution == oldDistribution
        assert newDescription.distribution == newDistribution
        assert diff.old == oldDistribution
        assert diff.new == newDistribution
        assert bc.old == oldDistribution
        assert bc.new == newDistribution

        cacheFile = self.cache / oldRelease.project / \
            f"{oldRelease}&{newRelease}.json"

        with Report(old=oldRelease, new=newRelease).produce(cacheFile, self.logger, redo=self.redo) as ret:
            if ret.creation is None or (ret.file and not ret.file.exists()):
                outFile = ret.file or cacheFile.with_suffix(".txt")
                with outFile.open("w") as out:
                    file = TeeFile(out, sys.stdout)

                    print("📜", oldRelease, newRelease, file=file)

                    distDuration: "timedelta" = oldDistribution.duration + newDistribution.duration
                    desDuration: "timedelta" = oldDescription.duration + newDescription.duration
                    print("\n⏱️ Duration", (distDuration + desDuration +
                          diff.duration + bc.duration).total_seconds(), file=file)
                    print(" ", "Preprocessing", distDuration, file=file)
                    print(" ", "Extracting", desDuration, file=file)
                    print(" ", "Differing", diff.duration, file=file)
                    print(" ", "Evaluating", bc.duration, file=file)

                    print("\n📝 Breaking Changes", end="", file=file)

                    for item in reversed(BreakingRank):
                        items = bc.rank(item)
                        if items:
                            print(" ", BCIcons[item], len(
                                items), end="", file=file)

                    print("\n", file=file)

                    changes = bc.breaking(BreakingRank.Low)
                    changes.sort(key=lambda x: x.rank, reverse=True)
                    for item in changes:
                        print(formatMessage(item), file=file)
                ret.file = outFile
            else:
                print(ret.file.read_text())

        return ret
