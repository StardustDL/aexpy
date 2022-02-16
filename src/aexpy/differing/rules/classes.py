from aexpy.models.description import ClassEntry
from ..checkers import DiffRule, DiffRuleCollection, RuleCheckResult, diffrule, fortype

from . import add, remove


ClassRules = DiffRuleCollection()

AddClass = DiffRule("AddClass", add).fortype(ClassEntry, True)
RemoveClass = DiffRule("RemoveClass", remove).fortype(ClassEntry, True)

ClassRules.rule(AddClass)
ClassRules.rule(RemoveClass)


@ClassRules.rule
@fortype(ClassEntry)
@diffrule
def ChangeBaseClass(a: ClassEntry, b: ClassEntry, **kwargs):
    sa = set(a.bases)
    sb = set(b.bases)
    plus = sb - sa
    minus = sa - sb
    message = []
    if len(plus) > 0:
        message.append(f"+ {', '.join(plus)}")
    if len(minus) > 0:
        message.append(f"- {', '.join(minus)}")
    if len(message) > 0:
        return RuleCheckResult(True, f"Change base classes ({a.id}): {'; '.join(message)}", {"add": plus, "remove": minus})
    return False


@ClassRules.rule
@fortype(ClassEntry)
@diffrule
def ChangeAbstractBaseClass(a: ClassEntry, b: ClassEntry, **kwargs):
    sa = set(a.abcs)
    sb = set(b.abcs)
    plus = sb - sa
    minus = sa - sb
    message = []
    if len(plus) > 0:
        message.append(f"+ {', '.join(plus)}")
    if len(minus) > 0:
        message.append(f"- {', '.join(minus)}")
    if len(message) > 0:
        return RuleCheckResult(True, f"Change abstract base classes ({a.id}): {'; '.join(message)}", {"add": plus, "remove": minus})
    return False
