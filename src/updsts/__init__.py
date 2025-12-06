# encoding: utf-8-sig

import sys
import io

# workaround for antigravity issues on Windows
if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer,
                                  encoding="utf-8",
                                  newline="\n",
                                  write_through=True)
