from aexpy.downloads import releases


def test_release(project):
    assert releases.getReleases(project)


def test_releaseInfo(projectVersion):
    project, version = projectVersion
    assert releases.getReleaseInfo(project, version)


def test_downloadInfo(projectVersion):
    project, version = projectVersion
    release = releases.getReleases(project)[version]
    assert releases.getDownloadInfo(release)


def test_compatibilityTag():
    tag = releases.getCompatibilityTag("jupyter-1.0.0-py2.py3-none-any.whl")
    assert tag.python == "py2.py3" and tag.abi == "none" and tag.platform[0] == "any"
