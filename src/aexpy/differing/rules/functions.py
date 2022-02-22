from aexpy.models.description import FunctionEntry

from ..checkers import DiffRule, DiffRuleCollection
from . import add, remove

FunctionRules = DiffRuleCollection()

AddFunction = DiffRule("AddFunction", add).fortype(FunctionEntry, True)
RemoveFunction = DiffRule(
    "RemoveFunction", remove).fortype(FunctionEntry, True)

FunctionRules.rule(AddFunction)
FunctionRules.rule(RemoveFunction)
