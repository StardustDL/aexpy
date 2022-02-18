from logging import Logger
from pathlib import Path
from uuid import uuid1

from aexpy.models import DiffEntry
from aexpy.producer import ProducerOptions

from .checkers import RuleEvaluator
from ..models import ApiDifference, ApiBreaking
from . import Evaluator as Base


class Evaluator(Base):
    def __init__(self, logger: "Logger | None" = None, cache: "Path | None" = None, options: "ProducerOptions | None" = None) -> None:
        super().__init__(logger, cache, options)
        self.evals: "list[RuleEvaluator]" = []

        from .evals import RuleEvals
        self.evals.extend(RuleEvals.ruleevals)

    def eval(self, diff: ApiDifference) -> ApiBreaking:
        cacheFile = self.cache / diff.old.release.project / \
            f"{diff.old.release}&{diff.new.release}.json" if self.cached else None

        with ApiBreaking(old=diff.old, new=diff.new).produce(cacheFile, self.logger, redo=self.redo) as ret:
            if ret.creation is None:
                for entry in diff.entries.values():
                    for rule in self.evals:
                        done: "list[DiffEntry]" = rule(entry, diff)
                        if done:
                            for item in done:
                                if not item.id:
                                    item.id = str(uuid1())
                            ret.entries.update({i.id: i for i in done})

        return ret
