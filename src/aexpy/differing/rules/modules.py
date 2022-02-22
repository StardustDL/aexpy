from aexpy.models.description import ModuleEntry

from ..checkers import DiffRule, DiffRuleCollection
from . import add, remove

ModuleRules = DiffRuleCollection()

AddModule = DiffRule("AddModule", add).fortype(ModuleEntry, True)
RemoveModule = DiffRule("RemoveModule", remove).fortype(ModuleEntry, True)

ModuleRules.rule(AddModule)
ModuleRules.rule(RemoveModule)
