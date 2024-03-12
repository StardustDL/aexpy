from typing import override

from ..utils import topLevelModules
from . import Preprocessor


class FileCounterPreprocessor(Preprocessor):
    @override
    def preprocess(self, /, product):
        assert product.rootPath, "No root path provided."

        if not product.topModules:
            product.topModules = list(topLevelModules(product.rootPath))

        product.fileCount = 0
        product.fileSize = 0
        product.locCount = 0

        for src in product.src:
            pyfiles = list(src.glob("**/*.py"))
            product.fileCount += len(pyfiles)
            for item in pyfiles:
                try:
                    product.fileSize += item.stat().st_size
                    product.locCount += len(item.read_text().splitlines())
                except Exception:
                    self.logger.error(f"Failed to stat file {item}.", exc_info=True)
