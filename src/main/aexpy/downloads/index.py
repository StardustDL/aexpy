from typing import List
import re
import json
from urllib import request
from .mirrors import INDEX_ORIGIN
from ..env import env
from .. import fsutils

def getIndex(url:str = INDEX_ORIGIN) -> List[str]:
    cache = env.cache.joinpath("index")
    fsutils.ensureDirectory(cache)
    resultCache = cache.joinpath("index.json")
    if resultCache.exists() and not env.redo:
        return json.loads(resultCache.read_text())
    htmlCache = cache.joinpath("simple.html")
    if not htmlCache.exists() or env.redo:
        try:
            with request.urlopen(url, timeout=60) as response:
                
                htmlCache.write_text(response.read().decode("utf-8"))
        except:
            raise Exception("No index")
    regex = r'<a href="[\w:/\.]*">([\S\s]*?)</a>'
    result = re.findall(regex, htmlCache.read_text())
    resultCache.write_text(json.dumps(result))
    return result
    