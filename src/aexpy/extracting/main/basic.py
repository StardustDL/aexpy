from datetime import datetime
import logging
import platform
import mypy
import sys
import json
from aexpy.models import ApiDescription, Distribution, Release


def main(dist: "Distribution"):
    result = ApiDescription(creation=datetime.now())
    return result


if __name__ == '__main__':
    logging.basicConfig(level=logging.NOTSET)
    dist = Distribution()
    dist.load(json.loads(sys.stdin.read()))
    print(main(dist).dumps())
