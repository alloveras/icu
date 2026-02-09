# Copyright (C) 2024 and later: Unicode, Inc. and others.
# License & terms of use: http://www.unicode.org/copyright.html

"""Bazel-compatible entry point for the databuilder.

This wrapper sets up the Python path correctly for Bazel's runfiles environment
before importing the main module.
"""

import os
import sys

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
PYTHON_ROOT = os.path.normpath(os.path.join(SCRIPT_PATH, "..", ".."))

if PYTHON_ROOT not in sys.path:
    sys.path.insert(0, PYTHON_ROOT)

from icutools.databuilder.__main__ import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
