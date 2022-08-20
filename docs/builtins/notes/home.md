---
name: home
creation: 2022-05-09 18:55:36.271649+08:00
modification: 2022-05-09 18:55:36.271649+08:00
targets: {}
tags: []
extra: {}
schema: 'dynamic:'
---

```python:exec
from pathlib import Path

print("""
This page describes how to get and use AexPy. We provide the experiment data at [Data](/data), and the full change patterns are given at [Change Specification](/change-spec).
""")
print("")

print(Path("../../../README.md").read_text())
```
