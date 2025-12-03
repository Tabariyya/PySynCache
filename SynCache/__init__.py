import sys

try:
    from ._core import *
    __all__ = ["Controller"]
except ImportError as e:
    print(f"Warning: Failed to load C++ extension: {e}")
    # You can add pure Python fallbacks here
    __all__ = []

__version__ = "1.0.4"