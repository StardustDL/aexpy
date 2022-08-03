---
name: Time Performance
creation: 2022-05-09 20:05:55.338390+08:00
modification: 2022-05-09 20:05:55.338390+08:00
targets:
  raw: ../assets/time.csv
tags: []
extra: {}
schema: 'dynamic:'
---

```python:exec
import csv
import sys
import os

print("# Table")

headers = "package,pidiff-avg,pidiff-max,pycompat-avg,pycompat-max,default-avg,default-max,size,loc".split(",")

guard = lambda s: "|" + s + "|"

print(guard("|".join(["No."] + headers)))
print(guard("|".join(["---"] * (len(headers)+1))))

count = {
    "pidiff": {
        "avg": 0,
        "max": 0,
    },
    "pycompat": {
        "avg": 0,
        "max": 0,
    },
    "default": {
        "avg": 0,
        "max": 0,
    },
}

def transform(row, k):
    if "-" in k:
        tool, type = k.split("-")
        count[tool][type] += float(row[k]) if row[k] else 0
    if k != "package":
        return f"{float(row[k]):.2f}"
    else:
        return row[k]

items = []

with open("../assets/time.csv", encoding="utf-8", mode="r") as f:
    reader = csv.DictReader(f)

    for i, row in enumerate(reader):
        items.append((
            float(row["loc"]),
            guard("|".join(["<id>"] + [transform(row, k) for k in headers]))
        ))

items.sort(key=lambda x: x[0])
for i, item in enumerate(items):
    print(item[1].replace("<id>", str(i+1)))

# print("# Stats")

# totalCount = {k: count[k]["High"] + count[k]["Medium"] for k in count}

# print(guard("|".join([""] + [f"{k}" for k in count])))
# print(guard("|".join(["---"] * (len(count)+1))))
# for level in ["High", "Medium"]:
#     print(guard("|".join([level] + [str(count[k][level]) for k in count])))
# print(guard("|".join(["**Total**"] + [f'{totalCount[k]} ({totalCount[k] / totalCount["Detect"]*100:.2f}%)' for k in totalCount])))
```
