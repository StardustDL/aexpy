import pytest
import aexpy.downloads.mirrors


PROJECTS = ["requests", "click"]

PROJECT_VERSIONS = [
    ("requests", "2.26.0"),
    ("requests", "2.25.1"),
    ("click", "8.0.3"),
    ("click", "8.0.1"),
]


@pytest.fixture(scope="module", params=PROJECTS)
def project(request):
    yield request.param


@pytest.fixture(scope="module", params=PROJECT_VERSIONS)
def projectVersion(request):
    yield request.param
