import json
import re
import urllib.request

FILE_ORIGIN = "https://files.pythonhosted.org/"
FILE_TSINGHUA = "https://pypi.tuna.tsinghua.edu.cn/"
INDEX_ORIGIN = "https://pypi.org/simple/"
INDEX_TSINGHUA = "https://pypi.tuna.tsinghua.edu.cn/simple/"


def getIndex(mirror: bool = False):
    req = urllib.request.Request(INDEX_TSINGHUA if mirror else INDEX_ORIGIN)
    with urllib.request.urlopen(req, timeout=60) as res:
        htmlContent = res.read().decode("utf-8")

    regex = r'<a href="[\w:/\.]*">([\S\s]*?)</a>'
    return re.findall(regex, htmlContent)


def getReleases(project: str) -> dict | None:
    try:
        req = urllib.request.Request(f"https://pypi.org/pypi/{project}/json")
        with urllib.request.urlopen(req, timeout=60) as res:
            text = res.read().decode("utf-8")
        return json.loads(text)["release"]
    except:
        return None


def getReleaseInfo(self, /, project: str, version: str) -> dict | None:
    try:
        req = urllib.request.Request(f"https://pypi.org/pypi/{project}/{version}/json")
        with urllib.request.urlopen(req, timeout=60) as res:
            text = res.read().decode("utf-8")
        return json.loads(text)["info"]
    except:
        return None
