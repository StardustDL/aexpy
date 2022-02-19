import random
import ssl
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from time import sleep
from typing import Any, Callable

from ..env import Options, env

from aexpy.models import Product

ssl._create_default_https_context = ssl._create_unverified_context


@dataclass
class ProcessItem:
    data: "Any"
    index: "int"
    total: "int"
    func: "Callable[[Any, bool], Product]"
    options: "Options"
    retry: "int" = 5
    stage: "str" = "Process"


def _process(item: "ProcessItem") -> "bool":
    try:
        env.reset(item.options)
        env.prepare()
        description = f"{item.data} ({item.index}/{item.total})"

        try:
            print(
                f"{item.stage} {description}.")

            count = 0
            while True:
                count += 1
                if count > item.retry:
                    break
                try:
                    print(f"  {item.stage}ing ({count} tries) {description}.")

                    res = item.func(item.data, count > 1)
                    assert res.success, "result is not successful"

                    break
                except Exception as ex:
                    print(
                        f"  Error Try {item.stage}ing ({count} tries) {description}: {ex}, retrying")
                    sleep(random.random())
            assert count <= item.retry, "too many retries"

            print(f"{item.stage}ed ({count} tries) {description}.")
            return True
        except Exception as ex:
            print(f"Error {item.stage} {description}: {ex}")
            return False
    except Exception as ex:
        print(f"Error {item.stage} {item}: {ex}")
        return False


class Processor:
    def __init__(self, processor: "Callable[[Any, bool], Product]") -> None:
        self.processor = processor

    def process(self, items: "list[Any]", workers: "int | None" = None, retry: "int" = 5, stage: "str" = "Process"):
        total = len(items)

        if total == 0:
            print("No items to process.")
            return

        todos = [ProcessItem(item, i+1, total, self.processor, env, retry, stage) for i, item in enumerate(items)]

        with ProcessPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(_process, todos))

        success = sum((1 for i in results if i))

        print(
            f"Processed {total} items, success {success} ({100*success/total}%).")
