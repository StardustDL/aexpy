from . import Preprocessor
from typing import override


class FileCounterPreprocessor(Preprocessor):
    @override
    def preprocess(self, product):
        assert product.rootPath, "No root path provided."

        for src in product.src:
            pyfiles = list(src.glob("**/*.py"))
            product.fileCount = len(pyfiles)
            product.fileSize = 0
            product.locCount = 0
            for item in pyfiles:
                try:
                    product.fileSize += item.stat().st_size
                    product.locCount += len(item.read_text().splitlines())
                except Exception as ex:
                    self.logger.error(f"Failed to stat file {item}.", exc_info=ex)
