from logging import Logger
import logging
import random
import ssl
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from time import sleep
from typing import Any, Callable

from ..env import Options, env

ssl._create_default_https_context = ssl._create_unverified_context


@dataclass
class ProcessItem:
    data: "Any"
    index: "int"
    total: "int"
    func: "Callable[[Any, bool], bool]"
    options: "Options"
    retry: "int" = 5
    stage: "str" = "Process"


def _process(item: "ProcessItem") -> "tuple[bool, str]":
    try:
        env.reset(item.options)
        env.prepare()
        description = f"{item.data} ({item.index}/{item.total})"

        try:
            # print(f"{item.stage} {description}.")

            count = 0
            while True:
                count += 1
                if count > item.retry:
                    break
                try:
                    # print(f"  {item.stage}ing ({count} tries) {description}.")

                    res = item.func(item.data, count > 1)
                    assert res, "result is not successful"

                    break
                except Exception as ex:
                    # print(f"  Error Try {item.stage}ing ({count} tries) {description}: {ex}, retrying")
                    sleep(random.random())
            assert count <= item.retry, "too many retries"

            # print(f"{item.stage}ed ({count} tries) {description}.")
            return True, f"{item.stage}ed ({count} tries) {description}."
        except Exception as ex:
            # print(f"Error {item.stage} {description}: {ex}")
            return False, f"Error {item.stage} {description}: {ex}"
    except Exception as ex:
        # print(f"Error {item.stage} {item}: {ex}")
        return False, f"Error {item.stage} {item}: {ex}"


class Processor:
    def __init__(self, processor: "Callable[[Any, bool], bool]", logger: "Logger | None" = None) -> None:
        self.logger = logger.getChild(
            "processor") if logger else logging.getLogger("processor")
        self.processor = processor

    def process(self, items: "list[Any]", workers: "int | None" = None, retry: "int" = 5, stage: "str" = "Process") -> "tuple[int,int]":
        total = len(items)

        if total == 0:
            self.logger.warning(f"No items to {stage}.")
            return 0, 0

        todos = [ProcessItem(item, i+1, total, self.processor,
                             env, retry, stage) for i, item in enumerate(items)]

        with ProcessPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(_process, todos))

        for i, item in enumerate(todos):
            success, message = results[i]
            if success:
                self.logger.info(f"{i}: {message}")
            else:
                self.logger.error(f"{i}: {message}")

        success = sum((1 for i, _ in results if i))

        self.logger.info(
            f"{stage}ed {total} items, success {success} ({100*success/total}%).")

        return success, total
