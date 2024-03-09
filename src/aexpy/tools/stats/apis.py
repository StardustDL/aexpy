from ...models import ApiDescription
from ...models.description import (ClassFlag, FunctionFlag, ItemScope,
                                   ParameterKind)
from . import ApiStatistician

S = ApiStatistician()

from .shared import duration, success

S.count(duration)
S.count(success)


@S.count
def private(data: ApiDescription):
    return sum(1 for e in data if e.private)


@S.count
def public(data: ApiDescription):
    return len(data) - private(data)


@S.count
def functions(data: ApiDescription):
    return len(data.functions)


@S.count
def classes(data: ApiDescription):
    return len(data.classes)


@S.count
def modules(data: ApiDescription):
    return len(data.modules)


@S.count
def attributes(data: ApiDescription):
    return len(data.attributes)


@S.count
def pri_functions(data: ApiDescription):
    return sum(1 for e in data.functions.values() if e.private)


@S.count
def pri_classes(data: ApiDescription):
    return sum(1 for e in data.classes.values() if e.private)


@S.count
def pri_modules(data: ApiDescription):
    return sum(1 for e in data.modules.values() if e.private)


@S.count
def pri_attributes(data: ApiDescription):
    return sum(1 for e in data.attributes.values() if e.private)


@S.count
def pub_functions(data: ApiDescription):
    return functions(data) - pri_functions(data)


@S.count
def pub_classes(data: ApiDescription):
    return classes(data) - pri_classes(data)


@S.count
def pub_modules(data: ApiDescription):
    return modules(data) - pri_modules(data)


@S.count
def pub_attributes(data: ApiDescription):
    return attributes(data) - pri_attributes(data)


@S.count
def abstract_classes(data: ApiDescription):
    return sum(1 for e in data.classes.values() if ClassFlag.Abstract in e.flags)


@S.count
def generic_classes(data: ApiDescription):
    return sum(1 for e in data.classes.values() if ClassFlag.Generic in e.flags)


@S.count
def final_classes(data: ApiDescription):
    return sum(1 for e in data.classes.values() if ClassFlag.Final in e.flags)


@S.count
def data_classes(data: ApiDescription):
    return sum(1 for e in data.classes.values() if ClassFlag.Dataclass in e.flags)


@S.count
def abstract_functions(data: ApiDescription):
    return sum(1 for e in data.functions.values() if FunctionFlag.Abstract in e.flags)


@S.count
def generic_functions(data: ApiDescription):
    return sum(1 for e in data.functions.values() if FunctionFlag.Generic in e.flags)


@S.count
def final_functions(data: ApiDescription):
    return sum(1 for e in data.functions.values() if FunctionFlag.Final in e.flags)


@S.count
def async_functions(data: ApiDescription):
    return sum(1 for e in data.functions.values() if FunctionFlag.Async in e.flags)


@S.count
def override_functions(data: ApiDescription):
    return sum(1 for e in data.functions.values() if FunctionFlag.Override in e.flags)


@S.count
def function_scopes(data: ApiDescription):
    return {
        scope.name: float(sum(1 for e in data.functions.values() if e.scope == scope))
        for scope in ItemScope
    }


@S.count
def attribute_scopes(data: ApiDescription):
    return {
        scope.name: float(sum(1 for e in data.attributes.values() if e.scope == scope))
        for scope in ItemScope
    }


@S.count
def parameters(data: ApiDescription):
    return sum(len(e.parameters) for e in data.functions.values())


@S.count
def parameter_kinds(data: ApiDescription):
    return {
        kind.name: float(
            sum(
                sum(1 for p in e.parameters if p.kind == kind)
                for e in data.functions.values()
            )
        )
        for kind in ParameterKind
    }


@S.count
def fixed_parameters(data: ApiDescription):
    counted = parameter_kinds(data)
    return sum(
        counted[k.name]
        for k in [
            ParameterKind.Keyword,
            ParameterKind.Positional,
            ParameterKind.PositionalOrKeyword,
        ]
    )


@S.count
def var_parameters(data: ApiDescription):
    return parameters(data) - fixed_parameters(data)


@S.count
def typed_parameters(data: ApiDescription):
    return sum(
        sum(1 for p in e.parameters if p.type is not None)
        for e in data.functions.values()
    )


@S.count
def untyped_parameters(data: ApiDescription):
    return parameters(data) - typed_parameters(data)


@S.count
def typed_functions(data: ApiDescription):
    return sum(
        1
        for e in data.functions.values()
        if e.returnType is not None or any(p.type is not None for p in e.parameters)
    )


@S.count
def untyped_functions(data: ApiDescription):
    return len(data.functions) - typed_functions(data)


@S.count
def typed_attributes(data: ApiDescription):
    return sum(1 for e in data.attributes.values() if e.type is not None)


@S.count
def untyped_attributes(data: ApiDescription):
    return len(data.attributes) - typed_attributes(data)
