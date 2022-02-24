from pathlib import Path
import sys
from aexpy import setCacheDirectory

if __name__ == "__main__":
    if len(sys.argv) > 1:
        setCacheDirectory(Path(sys.argv[1]))

    from .differ import main as main_differ
    main_differ()

    from .reader import main as main_reader
    main_reader()
