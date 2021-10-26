from aexpy.analyses.environment import analyze
from aexpy.analyses.models import ApiCollection, SpecialEntry, SpecialKind, ModuleEntry, ClassEntry, FunctionEntry, Parameter, ParameterKind, ApiManifest, FieldEntry
from aexpy.diffs.differ import Differ
from aexpy.diffs.environment import diff
from aexpy.downloads import releases, wheels
import pytest

PROJECT_VERSIONS = [
    ("requests", "2.25.1", "2.26.0"),
    ("click", "8.0.1", "8.0.3"),
]


@pytest.fixture(params=PROJECT_VERSIONS)
def projectDiffVersion(request):
    yield request.param


def test_rules():
    old = ApiCollection(ApiManifest("test", "1"))
    old.addEntry(ModuleEntry(id="mod"))
    old.addEntry(ModuleEntry(id="mod0", members={"m1": "", "m2": ""}))
    old.addEntry(ClassEntry(id="cls"))
    old.addEntry(ClassEntry(id="cls0", bases=["b1"]))
    old.addEntry(FunctionEntry(id="func"))
    old.addEntry(FunctionEntry(id="func0", returnType="str", parameters=[
        Parameter(ParameterKind.PositionalOrKeyword, name="a"),
        Parameter(ParameterKind.PositionalOrKeyword, name="c", optional=True),
        Parameter(ParameterKind.PositionalOrKeyword, name="e"),
        Parameter(ParameterKind.PositionalOrKeyword, name="f", optional=True),
        Parameter(ParameterKind.PositionalOrKeyword,
                  name="g", optional=True, default="1"),
        Parameter(ParameterKind.PositionalOrKeyword, name="h", type="int"),
        Parameter(ParameterKind.VarPositional, name="i"),
        Parameter(ParameterKind.VarKeyword, name="j"),
    ]))
    old.addEntry(FieldEntry(id="field"))
    old.addEntry(FieldEntry(id="field0", type="str"))

    new = ApiCollection(ApiManifest("test", "2"))
    new.addEntry(ModuleEntry(id="mod2"))
    new.addEntry(ModuleEntry(id="mod0", members={"m2": "changed", "m3": ""}))
    new.addEntry(ClassEntry(id="cls2"))
    new.addEntry(ClassEntry(id="cls0", bases=["b2"]))
    new.addEntry(FunctionEntry(id="func2"))
    new.addEntry(FunctionEntry(id="func0", returnType="int", parameters=[
        Parameter(ParameterKind.PositionalOrKeyword, name="b"),
        Parameter(ParameterKind.PositionalOrKeyword, name="d", optional=True),
        Parameter(ParameterKind.PositionalOrKeyword, name="e", optional=True),
        Parameter(ParameterKind.PositionalOrKeyword, name="f"),
        Parameter(ParameterKind.PositionalOrKeyword,
                  name="g", optional=True, default="2"),
        Parameter(ParameterKind.PositionalOrKeyword, name="h", type="str"),
    ]))
    new.addEntry(FieldEntry(id="field2"))
    new.addEntry(FieldEntry(id="field0", type="int"))

    result = Differ().with_default_rules().process(old, new)

    for item in result.entries.values():
        print(item.kind, item.message)

    assert len(result.entries) == 25


def test_diff(projectDiffVersion):
    project, old, new = projectDiffVersion
    rels = releases.getReleases(project)
    oldWheel, newWheel = list(
        map(wheels.downloadWheel, map(releases.getDownloadInfo, [rels[old], rels[new]])))

    oldResult, newResult = list(map(analyze, [oldWheel, newWheel]))

    result = diff(oldResult, newResult)
    assert result.entries
