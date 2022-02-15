import json
import re

import requests

import logging

from .. import utils
from ..env import env
from .mirrors import INDEX_ORIGIN

logger = logging.getLogger("download-index")


def getIndex(url: str = INDEX_ORIGIN) -> list[str]:
    cache = env.cache.joinpath("index")
    utils.ensureDirectory(cache)
    resultCache = cache.joinpath("index.json")
    if resultCache.exists() and not env.redo:
        return json.loads(resultCache.read_text())
    htmlCache = cache.joinpath("simple.html")
    if not htmlCache.exists() or env.redo:
        logger.info(f"Request PYPI Index @ {url}")
        try:
            htmlCache.write_text(requests.get(url, timeout=60).text)
        except Exception as ex:
            logger.error("Failed to request index", exc_info=ex)
            return []
    regex = r'<a href="[\w:/\.]*">([\S\s]*?)</a>'
    result = re.findall(regex, htmlCache.read_text())
    resultCache.write_text(json.dumps(result))
    return result
