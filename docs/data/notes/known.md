---
name: Detecting Known Breaking Changes
creation: 2022-05-09 20:05:49.228431+08:00
modification: 2022-05-09 20:05:49.228431+08:00
targets:
  raw: ../assets/known.csv
tags: []
extra: {}
schema: 'dynamic:'
---

```python:exec
import csv
import sys
import os

print("# Table")

headers = "issue,package,old,new,category,description,aexpy,pidiff,pycompat".split(",")

guard = lambda s: "|" + s + "|"

print(guard("|".join(["No."] + headers[1:])))
print(guard("|".join(["---"] * len(headers))))

cateCount = {}

count = {
    "aexpy": {
        "A": 0,
        "B": 0,
        "C": 0,
        "D": 0,
    },
    "pidiff": {
        "A": 0,
        "B": 0,
        "C": 0,
        "D": 0,
    },
    "pycompat": {
        "A": 0,
        "B": 0,
        "C": 0,
        "D": 0,
    },
}

def transform(row, k, i):
    if k == "issue":
        return f"[{i+1}]({row[k]})"
    elif k in {"aexpy", "pidiff", "pycompat"}:
        count[k][row[k]] += 1
        return {
            "A": "🟢", # A for detected
            "B": "🟡", # B for partial detected
            "C": "🟠", # C for not detected
            "D": "🔴", # D for crashed
        }[row[k]]
    elif k == "category":
        cateCount[row[k]] = cateCount.get(row[k], 0) + 1
    return row[k]

with open("../assets/known.csv", encoding="utf-8", mode="r") as f:
    reader = csv.DictReader(f)

    for i, row in enumerate(reader):
        print(guard("|".join([transform(row, k, i) for k in headers])))

print("# Category Stats")

print(guard("|".join(["category", "count"])))
print(guard("|".join(["---"] * 2)))
for k, v in sorted(cateCount.items(), key=lambda x: x[1], reverse=True):
    print(guard("|".join([k, str(v)])))

print("# Detection Stats")

total = sum(count["aexpy"].values())

print(guard("|".join(["Tool", "🟢 Detected", "🟡 Partial detected", "🟠 Not detected", "🔴 Crashed"])))
print(guard("|".join(["---"] * 5)))
for k, v in sorted(count.items(), key=lambda x: x[1]["A"] + x[1]["B"], reverse=True):
    print(guard("|".join([k, f'{v["A"]} ({(v["A"] / total) * 100:.2f}%)', f'{v["B"]} ({(v["B"] / total) * 100:.2f}%)', f'{v["C"]} ({(v["C"] / total) * 100:.2f}%)', f'{v["D"]} ({(v["D"] / total) * 100:.2f}%)'])))
```
