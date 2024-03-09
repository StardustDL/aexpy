from pathlib import Path

from .. import utils
from ..models import Release, ReleasePair


class DistPathBuilder:
    def __init__(self, /, root: Path) -> None:
        self.root = self.resolved(root)

    def resolved(self, /, path: Path):
        # utils.ensureDirectory(path.parent)
        return path.resolve()

    def preprocess(self, /, release: Release):
        return self.resolved(
            self.distributionDir(release.project) / f"{release.version}.json"
        )

    def extract(self, /, release: Release):
        return self.resolved(self.apiDir(release.project) / f"{release.version}.json")

    def diff(self, /, pair: ReleasePair):
        assert (
            pair.old.project == pair.new.project
        ), f"ReleasePair not same project: {pair}"
        return self.resolved(
            self.changeDir(pair.old.project)
            / f"{pair.old.version}&{pair.new.version}.json"
        )

    def report(self, /, pair: ReleasePair):
        assert (
            pair.old.project == pair.new.project
        ), f"ReleasePair not same project: {pair}"
        return self.resolved(
            self.reportDir(pair.old.project)
            / f"{pair.old.version}&{pair.new.version}.json"
        )

    def projects(self):
        for item in self.root.glob("*"):
            if item.is_dir():
                yield item.stem

    def projectDir(self, /, project: str):
        return self.root / project

    def distributionDir(self, /, project: str):
        return self.projectDir(project) / "distributions"

    def apiDir(self, /, project: str):
        return self.projectDir(project) / "apis"

    def changeDir(self, /, project: str):
        return self.projectDir(project) / "changes"

    def reportDir(self, /, project: str):
        return self.projectDir(project) / "reports"

    def distributions(self, /, project: str):
        dir = self.distributionDir(project)
        if not dir.is_dir():
            return
        for item in dir.glob("*.json"):
            yield Release(project=project, version=item.stem)

    def apis(self, /, project: str):
        dir = self.apiDir(project)
        if not dir.is_dir():
            return
        for item in dir.glob("*.json"):
            yield Release(project=project, version=item.stem)

    def changes(self, /, project: str):
        dir = self.changeDir(project)
        if not dir.is_dir():
            return
        for item in dir.glob("*.json"):
            old, new = item.stem.split("&", maxsplit=1)
            yield ReleasePair(
                old=Release(project=project, version=old),
                new=Release(project=project, version=new),
            )

    def reports(self, /, project: str):
        dir = self.reportDir(project)
        if not dir.is_dir():
            return
        for item in dir.glob("*.json"):
            old, new = item.stem.split("&", maxsplit=1)
            yield ReleasePair(
                old=Release(project=project, version=old),
                new=Release(project=project, version=new),
            )
