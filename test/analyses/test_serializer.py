from aexpy.analyses.models import ApiCollection, SpecialEntry, SpecialKind, ModuleEntry, ClassEntry, FunctionEntry, Parameter, ParameterKind
from aexpy.analyses.serializer import serialize, deserialize


def test_serializer():
    collection = ApiCollection()
    collection.addEntry(SpecialEntry(
        id="extenal", kind=SpecialKind.External, data="data"))
    collection.addEntry(ModuleEntry(id="module", members={
        "func": "func",
        "class": "class"
    }))
    collection.addEntry(ClassEntry(id="class", bases=["base"], members={
        "func": "func"
    }))
    collection.addEntry(FunctionEntry(id="func", bound=False, returnType="None", parameters=[
        Parameter(ParameterKind.Positional, "para", "str", "empty", True),
    ]))

    text = serialize(collection)
    print(text)

    raw = deserialize(text)

    entries = list(raw.entries.values())

    assert entries[0].kind is SpecialKind.External
    assert entries[3].parameters[0].kind is ParameterKind.Positional

    print(serialize(raw))

    assert serialize(raw) == text
