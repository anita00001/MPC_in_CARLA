#!/usr/bin/env python3
"""Display Python interpreter and operating-system information."""

from __future__ import annotations

import os
import platform
import shutil
import sys


def main() -> int:
    print("=" * 70)
    print("PYTHON AND OPERATING SYSTEM")
    print("=" * 70)

    print(f"Python executable : {sys.executable}")
    print(f"Python version    : {sys.version}")
    print(f"Version tuple     : {sys.version_info}")
    print(f"Operating system  : {platform.platform()}")
    print(f"System            : {platform.system()}")
    print(f"Machine           : {platform.machine()}")
    print(f"Architecture      : {platform.architecture()[0]}")
    print(f"Current directory : {os.getcwd()}")

    print("\nInterpreter commands found:")

    for command in ("python", "python3"):
        path = shutil.which(command)

        if path is None:
            print(f"  {command:<8}: not found")
        else:
            print(f"  {command:<8}: {path}")

    if sys.version_info < (3, 10):
        print("\nWARNING: Python is older than 3.10.")
        return 1

    print("\nPASS: Python and operating-system information was read.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
