import sys

from aexpy.models import Release

from .releases import projects

from .single import SingleProcessor
from .pair import PairProcessor

if __name__ == "__main__":
    # from . import default
    # SingleProcessor(default.pre).processVersion("coxbuild", "0.0.9")
    # exit(0)

    if sys.argv[-2] == "default":
        from . import default
    elif sys.argv[-2] == "pidiff":
        from . import pidiff as default
    elif sys.argv[-2] == "pycompat":
        from . import pycompat as default
    else:
        raise ValueError("Unknown processor: " + sys.argv[-2])

    if sys.argv[-1] == "pre":
        SingleProcessor(default.pre).processProjects(projects)
    elif sys.argv[-1] == "ext":
        SingleProcessor(default.ext).processProjects(projects)
    elif sys.argv[-1] == "dif":
        PairProcessor(default.dif).processProjects(projects)
    elif sys.argv[-1] == "eva":
        PairProcessor(default.eva).processProjects(projects)
    elif sys.argv[-1] == "rep":
        PairProcessor(default.rep).processProjects(projects)
    elif sys.argv[-1] == "ana":
        SingleProcessor(default.ext).processProjects(projects)
        PairProcessor(default.dif).processProjects(projects)
        PairProcessor(default.eva).processProjects(projects)
        PairProcessor(default.rep).processProjects(projects)
    elif sys.argv[-1] == "all":
        SingleProcessor(default.pre).processProjects(projects)
        SingleProcessor(default.ext).processProjects(projects)
        PairProcessor(default.dif).processProjects(projects)
        PairProcessor(default.eva).processProjects(projects)
        PairProcessor(default.rep).processProjects(projects)
    else:
        raise Exception(f"Unknown command {sys.argv[-1]}")
