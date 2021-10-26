import pytest
from aexpy.downloads import index
from aexpy.downloads.mirrors import FILE_ORIGIN, FILE_TSINGHUA, INDEX_ORIGIN, INDEX_TSINGHUA


@pytest.fixture(params=[INDEX_ORIGIN, INDEX_TSINGHUA])
def indexMirror(request):
    yield request.param


def test_index(indexMirror):
    pass
    # assert index.getIndex(indexMirror)
