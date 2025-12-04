"""
PySynCache - Python bindings for SynCache distributed caching system
"""

import sys

try:
    from ._core import Controller
    __all__ = ["Controller"]
except ImportError as e:
    # Provide helpful error message for missing extension
    print(f"Error loading C++ extension: {e}")
    print("This package requires compilation. Make sure you have:")
    print("1. A C++ compiler (g++, clang++, or MSVC)")
    print("2. Python development headers")
    print("3. pybind11 installed in build environment")
    raise

__version__ = "1.0.0"
