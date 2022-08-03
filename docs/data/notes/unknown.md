---
name: Finding Unknown Breaking Changes
creation: 2022-05-09 20:05:55.338390+08:00
modification: 2022-05-09 20:05:55.338390+08:00
targets:
  raw: ../assets/unknown.csv
tags: []
extra: {}
schema: 'dynamic:'
---

```python:exec
import csv
import sys
import os

print("# Table")

headers = "package,previous,latest,High-Detect,Medium-Detect,High-TP,Medium-TP,High-Undocument,Medium-Undocument,High-Report,Medium-Report,High-Confirm,Medium-Confirm".split(",")

guard = lambda s: "|" + s + "|"

print(guard("|".join(["No."] + headers)))
print(guard("|".join(["---"] * (len(headers)+1))))

count = {
    "Detect": {
        "High": 0,
        "Medium": 0,
    },
    "TP": {
        "High": 0,
        "Medium": 0,
    },
    "FP": {
        "High": 0,
        "Medium": 0,
    },
    "Document": {
        "High": 0,
        "Medium": 0,
    },
    "Undocument": {
        "High": 0,
        "Medium": 0,
    },
    "Report": {
        "High": 0,
        "Medium": 0,
    },
    "Confirm": {
        "High": 0,
        "Medium": 0,
    },
}

def transform(row, k):
    if "-" in k:
        level, type = k.split("-")
        count[type][level] += int(row[k]) if row[k] else 0
    return row[k]

items = []

with open("../assets/unknown.csv", encoding="utf-8", mode="r") as f:
    reader = csv.DictReader(f)

    for i, row in enumerate(reader):
        items.append((
            int(row["High-Detect"] or 0) + int(row["Medium-Detect"] or 0),
            guard("|".join(["<id>"] + [transform(row, k) for k in headers]))
        ))

items.sort(key=lambda x: x[0])
for i, item in enumerate(items):
    print(item[1].replace("<id>", str(i+1)))

for level in ["High", "Medium"]:
    count["FP"][level] = count["Detect"][level] - count["TP"][level]
    count["Document"][level] = count["TP"][level] - count["Undocument"][level]

print("# Stats")

totalCount = {k: count[k]["High"] + count[k]["Medium"] for k in count}

print(guard("|".join([""] + [f"{k}" for k in count])))
print(guard("|".join(["---"] * (len(count)+1))))
for level in ["High", "Medium"]:
    print(guard("|".join([level] + [str(count[k][level]) for k in count])))
print(guard("|".join(["**Total**"] + [f'{totalCount[k]} ({totalCount[k] / totalCount["Detect"]*100:.2f}%)' for k in totalCount])))
```
