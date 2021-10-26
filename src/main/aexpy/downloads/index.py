import json
import re
import requests

from .. import fsutils
from ..env import env
from .mirrors import INDEX_ORIGIN


def getIndex(url: str = INDEX_ORIGIN) -> list[str]:
    cache = env.cache.joinpath("index")
    fsutils.ensureDirectory(cache)
    resultCache = cache.joinpath("index.json")
    if resultCache.exists() and not env.redo:
        return json.loads(resultCache.read_text())
    htmlCache = cache.joinpath("simple.html")
    if not htmlCache.exists() or env.redo:
        try:
            htmlCache.write_text(requests.get(url, timeout=60).text)
        except:
            raise Exception("No index")
    regex = r'<a href="[\w:/\.]*">([\S\s]*?)</a>'
    result = re.findall(regex, htmlCache.read_text())
    resultCache.write_text(json.dumps(result))
    return result
