import pathlib

PACKAGE_Dir = pathlib.Path("/package")
STUB_Dir = PACKAGE_Dir.joinpath("stubs")
UNPACKED_Dir = PACKAGE_Dir.joinpath("unpacked")

OUTPUT_PREFIX = "START_AEXPY_ANALYZER_OUTPUT"
