import os
import subprocess
from pathlib import Path
from aexpy.environments.conda import CondaEnvironment
from aexpy.models import Distribution
from .wheel import INDEX_ORIGIN, INDEX_TSINGHUA, WheelPreprocessor


class PipPreprocessor(WheelPreprocessor):
    def downloadWheel(self, distribution: "Distribution", path: "Path") -> "Path":
        index = INDEX_TSINGHUA if self.mirror else INDEX_ORIGIN

        release = distribution.release

        files = list(path.glob(f"{release.project}-{release.version}*.whl"))
        for item in files:
            if item.is_file():
                os.remove(item)
        for pyver in range(10, 6, -1):
            pyversion = f"3.{pyver}"
            self.logger.info(
                f"Download wheel distribution for Python {pyversion}.")
            try:
                subres = subprocess.run(["pip", "download", "--python-version", pyversion,
                                         f"{release.project}=={release.version}", "--no-deps", "--only-binary", ":all:", "-i", index], cwd=path, capture_output=True, text=True)
                self.logger.info(
                    f"Inner pip download wheel for Python {pyversion} exit with {subres.returncode}.")
                if subres.stdout.strip():
                    self.logger.debug(f"STDOUT:\n{subres.stdout}")
                if subres.stderr.strip():
                    self.logger.info(f"STDERR:\n{subres.stderr}")
                files = list(
                    path.glob(f"{release.project}-{release.version}*.whl"))
                assert len(files) > 0
                distribution.pyversion = pyversion
                return files[0].resolve()
            except Exception as ex:
                self.logger.error(
                    f"Failed to download for Python {pyversion} wheel for {release}", exc_info=ex)

        files = list(path.glob(f"{release.project}-{release.version}*.tar.gz"))
        for item in files:
            if item.is_file():
                os.remove(item)
        for pyver in range(10, 6, -1):
            pyversion = f"3.{pyver}"
            self.logger.info(
                f"Download source distribution for Python {pyversion}.")
            try:
                subres = subprocess.run(["pip", "download", "--python-version", pyversion,
                                         f"{release.project}=={release.version}", "--no-deps", "--no-binary", ":all:", "-i", index], cwd=path, capture_output=True, text=True)
                self.logger.info(
                    f"Inner pip download sdist for Python {pyversion} exit with {subres.returncode}.")
                if subres.stdout.strip():
                    self.logger.debug(f"STDOUT:\n{subres.stdout}")
                if subres.stderr.strip():
                    self.logger.info(f"STDERR:\n{subres.stderr}")

                files = list(
                    path.glob(f"{release.project}-{release.version}*.tar.gz"))
                assert len(files) > 0

                with CondaEnvironment(pyversion) as run:
                    self.logger.info(
                        f"Build wheel distribution for Python {pyversion}: {files[0]}.")
                    subres = run(
                        f"pip wheel {release.project}=={release.version} --no-deps -i {index}", cwd=path, capture_output=True, text=True)
                    self.logger.info(
                        f"Inner pip wheel {files[0]} exit with {subres.returncode}.")
                    if subres.stdout.strip():
                        self.logger.debug(f"STDOUT:\n{subres.stdout}")
                    if subres.stderr.strip():
                        self.logger.info(f"STDERR:\n{subres.stderr}")

                files = list(
                    path.glob(f"{release.project}-{release.version}*.whl"))
                assert len(files) > 0

                distribution.pyversion = pyversion
                return files[0].resolve()
            except Exception as ex:
                self.logger.error(
                    f"Failed to download source dist for Python {pyversion} for {release}", exc_info=ex)
