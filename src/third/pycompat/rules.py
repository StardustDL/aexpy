from aexpy.differing.checkers import RuleCheckResult, diffrule, fortype
from aexpy.models.description import FunctionEntry
from aexpy.models.difference import BreakingRank


@fortype(FunctionEntry)
@diffrule
def AddRequiredParameter(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = a.parameters
    pb = b.parameters

    new = set(pb) - set(pa)

    items = []

    for item in new:
        if not b.getParameter(item).optional:
            items.append(item)

    if items:
        return RuleCheckResult(True, f"Add required parameters: {'; '.join(items)}")

    return False


@fortype(FunctionEntry)
@diffrule
def RemoveRequiredParameter(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = a.parameters
    pb = b.parameters

    new = set(pa) - set(pb)

    items = []

    for item in new:
        if not a.getParameter(item).optional:
            items.append(item)

    if items:
        return RuleCheckResult(True, f"Remove required parameters: {'; '.join(items)}")

    return False


@fortype(FunctionEntry)
@diffrule
def AddOptionalParameter(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = a.parameters
    pb = b.parameters

    new = set(pb) - set(pa)

    items = []

    for item in new:
        if b.getParameter(item).optional:
            items.append(item)

    if items:
        return RuleCheckResult(True, f"Add optional parameters: {'; '.join(items)}")

    return False


@fortype(FunctionEntry)
@diffrule
def RemoveOptionalParameter(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = a.parameters
    pb = b.parameters

    new = set(pa) - set(pb)

    items = []

    for item in new:
        if a.getParameter(item).optional:
            items.append(item)

    if items:
        return RuleCheckResult(True, f"Remove optional parameters: {'; '.join(items)}")

    return False


@fortype(FunctionEntry)
@diffrule
def ReorderParameter(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = a.parameters
    pb = b.parameters

    new = set(pa) & set(pb)

    items = []

    for item in new:
        for titem in new:
            if item == titem:
                continue
            if pa.index(item) < pa.index(titem) and pb.index(item) > pb.index(titem):
                items.append((item, titem))

    if items:
        return RuleCheckResult(True, f"Reorder parameters: {'; '.join(items)}")

    return False


@fortype(FunctionEntry)
@diffrule
def AddParameterDefault(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = a.parameters
    pb = b.parameters

    new = set(pa) & set(pb)

    items = []

    for item in new:
        if not a.getParameter(item).optional and b.getParameter(item).optional:
            items.append(item)

    if items:
        return RuleCheckResult(True, f"Add parameter default: {'; '.join(items)}")

    return False


@fortype(FunctionEntry)
@diffrule
def RemoveParameterDefault(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = a.parameters
    pb = b.parameters

    new = set(pa) & set(pb)

    items = []

    for item in new:
        if a.getParameter(item).optional and not b.getParameter(item).optional:
            items.append(item)

    if items:
        return RuleCheckResult(True, f"Remove parameter default: {'; '.join(items)}")

    return False


@fortype(FunctionEntry)
@diffrule
def ChangeParameterDefault(a: "FunctionEntry", b: "FunctionEntry", **kwargs):
    pa = a.parameters
    pb = b.parameters

    new = set(pa) & set(pb)

    items = []

    for item in new:
        if a.getParameter(item).optional and b.getParameter(item).optional:
            da = a.getParameter(item).default
            db = b.getParameter(item).default
            if da != "___complex_type___" and db != "___complex_type___" and da != db:
                items.append((item, da, db))

    if items:
        return RuleCheckResult(True, f"Change parameter default: {'; '.join(items)}")

    return False
