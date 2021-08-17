import libaqua.cli
import sys
if sys.argv[0].endswith("__main__.py"):
    import os.path
    executable = os.path.basename(sys.executable)
    sys.argv[0] = executable + " -m libaqua"
    del os

libaqua.cli.app()

