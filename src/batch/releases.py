from aexpy.models import Release


projects = ["urllib3", "python-dateutil", "requests", "pyyaml", "jmespath",
            "numpy", "click", "pandas", "flask", "tornado", "django", "scrapy", "coxbuild"]

# projects = ["coxbuild"]


def getReleases(project: str) -> "list[Release]":
    from aexpy.preprocessing.default import Preprocessor

    prep = Preprocessor()

    rels = []

    for version in prep.getReleases(project):
        rels.append(Release(project, version))

    return rels
