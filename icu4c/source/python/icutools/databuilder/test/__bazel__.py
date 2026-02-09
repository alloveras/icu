# Copyright (C) 2024 and later: Unicode, Inc. and others.
# License & terms of use: http://www.unicode.org/copyright.html

"""Bazel-compatible entry point for the databuilder tests.

This wrapper sets up the Python path correctly for Bazel's runfiles environment
before importing the tests' main module.
"""

import os
import sys
import unittest

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
PYTHON_ROOT = os.path.normpath(os.path.join(SCRIPT_PATH, "..", "..", ".."))

if PYTHON_ROOT not in sys.path:
    sys.path.insert(0, PYTHON_ROOT)

# Import the original test module and delegate to it.
from icutools.databuilder.test import __main__ as test_module

if __name__ == "__main__":
    unittest.main(module=test_module)
