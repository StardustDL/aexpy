from datetime import datetime
import psutil
from time import sleep

while True:
    mem = psutil.virtual_memory()
    total = float(mem.total) / 1024**3
    used = float(mem.used) / 1024**3
    free = float(mem.free) / 1024**3
    rate = used / total
    if rate > 0.7:
        print(datetime.now(), total, used, free,
            f"{rate * 100:.2f}%", sep="\t")
    sleep(1)
