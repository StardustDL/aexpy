import dataclasses
import logging
import multiprocessing
import random
import ssl
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from logging import Logger
from time import sleep
from typing import Any, Callable, Generic, TypeVar

from ..env import Configuration, env

ssl._create_default_https_context = ssl._create_unverified_context


@dataclass
class ProcessItem:
    data: "Any"
    index: "int"
    total: "int"
    func: "Callable[[Any, Configuration, bool], bool]"
    options: "Configuration"
    retry: "int" = 3
    stage: "str" = "Process"


def _process(item: "ProcessItem") -> "tuple[bool, str]":
    try:
        env.reset(item.options)
        env.prepare()
        description = f"{item.data} ({item.index}/{item.total})"

        try:
            # print(f"{item.stage} {description}.")

            count = 0
            steplogs = []
            while True:
                count += 1
                if count > item.retry:
                    break

                p = multiprocessing.Process(
                    target=item.func, args=(item.data, item.options, count > 1), daemon=True)

                try:
                    # print(f"  {item.stage}ing ({count} tries) {description}.")

                    p.start()
                    # wait for 1 hour
                    p.join(60*60)

                    assert not p.is_alive(), f"{item.stage.lower()}ing timeout"

                    assert p.exitcode == 0, "result is not successful"

                    break
                except Exception as ex:
                    # print(f"  Error Try {item.stage}ing ({count} tries) {description}: {ex}, retrying")
                    steplogs.append(str(ex))
                    sleep(random.random())
                finally:
                    p.kill()
                    p.join()
                    p.close()
            assert count <= item.retry, f"too many retries: {', '.join(steplogs)}"

            # print(f"{item.stage}ed ({count} tries) {description}.")
            return True, f"{item.stage}ed ({count} tries) {description}: {', '.join(steplogs) or 'empty'}."
        except Exception as ex:
            # print(f"Error {item.stage} {description}: {ex}")
            return False, f"Error {item.stage} {description}: {ex}"
    except Exception as ex:
        # print(f"Error {item.stage} {item}: {ex}")
        return False, f"Error {item.stage} {item}: {ex}"


T = TypeVar("T")


class Processor(Generic[T]):
    def __init__(self, processor: "Callable[[T, Configuration, bool], None]", logger: "Logger | None" = None) -> None:
        self.logger = logger.getChild(
            "processor") if logger else logging.getLogger("processor")
        self.processor = processor

    def process(self, items: "list[T]", workers: "int | None" = None, retry: "int" = 3, stage: "str" = "Process", provider: "str | None" = None) -> "tuple[list[T], list[T]]":
        total = len(items)

        if total == 0:
            self.logger.warning(f"No items to {stage}.")
            return [], []

        if provider:
            realEnv = dataclasses.replace(env, provider=provider)
        else:
            realEnv = dataclasses.replace(env)

        todos = [ProcessItem(item, i+1, total, self.processor,
                             realEnv, retry, stage) for i, item in enumerate(items)]

        with ProcessPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(_process, todos))

        successed: "list[T]" = []
        failed: "list[T]" = []

        for i, item in enumerate(todos):
            success, message = results[i]
            if success:
                successed.append(item.data)
                self.logger.info(f"{i}: {message}")
            else:
                failed.append(item.data)
                self.logger.error(f"{i}: {message}")

        self.logger.info(
            f"{stage}ed {total} items, success {len(successed)} ({100*len(successed)/total}%).")

        return successed, failed
