# Copyright (C) 2024 and later: Unicode, Inc. and others.
# License & terms of use: http://www.unicode.org/copyright.html

"""Bazel-compatible entry point for the databuilder.

This wrapper sets up the Python path correctly for Bazel's runfiles environment
before importing the main module.
"""

import os
import sys

# Find the python directory relative to this file and add it to sys.path
# This script is at: icu4c/source/python/icutools/databuilder/databuilder_entry.py
# The python dir is at: icu4c/source/python/
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PYTHON_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
if _PYTHON_DIR not in sys.path:
    sys.path.insert(0, _PYTHON_DIR)

from icutools.databuilder.__main__ import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
