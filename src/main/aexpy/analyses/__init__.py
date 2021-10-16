import pathlib

PACKAGE_Dir = pathlib.Path("/package")
STUB_Dir = PACKAGE_Dir.joinpath("stubs")
UNPACKED_Dir = PACKAGE_Dir.joinpath("unpacked")