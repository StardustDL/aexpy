from aexpy.models.description import AttributeEntry
from ..checkers import DiffRule, DiffRuleCollection, fortype, diffrule, RuleCheckResult
from . import add, remove


AttributeRules = DiffRuleCollection()

AddAttribute = DiffRule("AddAttribute", add).fortype(AttributeEntry, True)
RemoveAttribute = DiffRule(
    "RemoveAttribute", remove).fortype(AttributeEntry, True)

AttributeRules.rule(AddAttribute)
AttributeRules.rule(RemoveAttribute)