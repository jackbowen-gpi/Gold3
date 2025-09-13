import sys

import pytest

# Use pytest to collect initial conftest files
args = ["--pyargs"]
# We'll just print sys.path and exit
print("sys.path (first 10):", sys.path[:10])
# Try to use pytest to load conftests via helper
print("pytest version", pytest.__version__)
