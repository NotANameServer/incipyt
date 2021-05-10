import os
import sys

# Remove '' and current working directory from the first entry
# of sys.path, if present to avoid using current directory
# in incipyt commands, when invoked as python -m incipyt <command>
if sys.path[0] in ("", os.getcwd()):
    sys.path.pop(0)

if __name__ == "__main__":
    from incipyt.cli import main as _main

    sys.exit(_main())
