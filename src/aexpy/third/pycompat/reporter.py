from pathlib import Path

from aexpy.reporting.generators import GeneratorReporter


class Reporter(GeneratorReporter):
    def defaultCache(self) -> "Path | None":
        return super().defaultCache() / "pycompat"
