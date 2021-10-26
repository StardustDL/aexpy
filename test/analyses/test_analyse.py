from aexpy.analyses.environment import analyze
from aexpy.downloads import releases, wheels


def test_analyze(projectVersion):
    project, version = projectVersion
    release = releases.getReleases(project)[version]
    dinfo = releases.getDownloadInfo(release)
    wheel = wheels.downloadWheel(dinfo)

    result = analyze(wheel)
    assert result.entries
