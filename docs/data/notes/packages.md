---
name: Selected Packages
creation: 2022-05-11 16:13:18.256454+08:00
modification: 2022-05-11 16:13:18.256454+08:00
targets: {}
tags: []
extra: {}
schema: 'dynamic:'
---

```python:exec
from urllib.request import urlopen
import json

data = [
    ("bentoml", "bentoml/BentoML"),
    ("clyngor", "Aluriak/clyngor"),
    ("flask", "pallets/flask"),
    ("betfairlightweight", "betcode-org/betfair"),
    ("catkin-tools", "catkin/catkin_tools"),
    ("click", "pallets/click"),
    ("docspec", "NiklasRosenstein/docspec"),
    ("meshio", "nschloe/meshio"),
    ("paramiko", "paramiko/paramiko"),
    ("requests", "psf/requests"),
    ("resolvelib", "sarugaku/resolvelib"),
    ("scrapy", "scrapy/scrapy"),
    ("markupsafe", "pallets/markupsafe"),
    # ("streamz", "python-streamz/streamz"),
    ("pandas", "pandas-dev/pandas"),
    ("numpy", "numpy/numpy"),
    ("Django", "django/django"),
    ("matplotlib", "matplotlib/matplotlib"),
    ("trio", "python-trio/trio"),
    ("python-dateutil", "dateutil/dateutil"),
    ("asyncpg", "MagicStack/asyncpg"),
    ("urllib3", "urllib3/urllib3"),
    ("pooch", "fatiando/pooch"),
    ("jmespath", "jmespath/jmespath.py"),
    ("pystac", "stac-utils/pystac"),
    ("pyyaml", "yaml/pyyaml"),
    ("harvesters", "genicam/harvesters"),
    ("pyjwt", "jpadilla/pyjwt"),
    ("humanize", "python-humanize/humanize"),
    ("jinja2", "pallets/jinja"),
    ("captum", "pytorch/captum"),
    ("ao3", "ArmindoFlores/ao3_api"),
    ("xarray", "pydata/xarray"),
    ("pecanpy", "krishnanlab/PecanPy"),
    ("gradio", "gradio-app/gradio"),
    ("diffsync", "networktocode/diffsync"),
    ("rpyc", "tomerfiliba-org/rpyc"),
    ("evidently", "evidentlyai/evidently"),
    ("prompt-toolkit", "prompt-toolkit/python-prompt-toolkit"),
    ("tornado", "tornadoweb/tornado"),
    ("pybinance", "sammchardy/python-binance"),
    ("astroquery", "astropy/astroquery"),
    ("pyoverkiz", "iMicknl/python-overkiz-api"),
    ("appcenter", "microsoft/appcenter-rest-python"),
    ("stonesoup", "dstl/Stone-Soup"),
    ("scikit-learn", "scikit-learn/scikit-learn"),
]

def getstars(repo):
    try:
        with urlopen(f"https://api.github.com/repos/{repo}") as response:
            data = json.loads(response.read())
            return data["stargazers_count"]
    except:
        return -1
    

def getdownloads(name):
    with urlopen(f"https://api.pepy.tech/api/v2/projects/{name}") as response:
        data = json.loads(response.read())
        return data["total_downloads"]

def getinfo(name):
    try:
        with urlopen(f"https://pypi.org/pypi/{name}/json") as response:
            data = json.loads(response.read())
            return data["info"]["summary"], len(data["releases"])
    except:
        return "Not Found", -1


result = []
for name, repo in data:
    stars = getstars(repo)
    summary, versions = getinfo(name)
    result.append((name, repo, summary, versions, stars))
result.sort(key=lambda x: x[-1], reverse=True)

print(f"# {len(result)} Packages")
print(f"- Min stars: {result[-1][-1]}")
print(f"- Max stars: {result[0][-1]}")
print(f"- Average stars: {sum(x[-1] for x in result) / len(result)}")

print("# Table")
print("| Package | Versions | Repo | Stars | Summary |")
print("| --- | --- | --- | --- | --- |")

for name, repo, summary, versions, stars in result:
    print(f"| [{name}](https://pypi.org/project/{name}) | {versions} | [{repo}](https://github.com/{repo}) | {stars} | {summary} |")
```