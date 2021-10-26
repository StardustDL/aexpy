from aexpy.downloads import wheels, releases
from aexpy.downloads.mirrors import FILE_ORIGIN, FILE_TSINGHUA
import pytest


@pytest.fixture(params=[FILE_ORIGIN, FILE_TSINGHUA])
def fileMirror(request):
    yield request.param


def test_downloadUnpack(projectVersion, fileMirror):
    project, version = projectVersion
    release = releases.getReleases(project)[version]
    dinfo = releases.getDownloadInfo(release)
    wheel = wheels.downloadWheel(dinfo, fileMirror)
    unpacked = wheels.unpackWheel(wheel)

    distInfo = wheels.getDistInfo(unpacked)
    assert distInfo

    assert wheels.getAvailablePythonVersion(distInfo)
