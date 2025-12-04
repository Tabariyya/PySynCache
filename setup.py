from setuptools import setup, Extension, find_packages
import platform
from pathlib import Path
import sys
import subprocess
import os


def get_pybind11_include():
    """Get pybind11 include directory."""
    # First try to import
    try:
        import pybind11
        return pybind11.get_include()
    except ImportError:
        # During pip install, pybind11 should be available from build-system
        # If not, provide a helpful error
        raise RuntimeError(
            "pybind11 is required to build this package. "
            "Make sure it's installed in your build environment."
        )


def get_extension():
    """Create extension for the current platform."""

    # Get current platform
    system = platform.system().lower()
    arch = platform.machine().lower()

    print(f"Building for platform: {system}/{arch}")

    platform_map = {
        'linux': 'linux',
        'darwin': 'macOS',  # Your directory uses capital S
        'windows': 'windows'
    }

    arch_map = {
        'x86_64': 'x64',
        'amd64': 'x64',
        'arm64': 'arm64',
        'aarch64': 'arm64'
    }

    current_platform = platform_map.get(system)
    current_arch = arch_map.get(arch)

    if not current_platform:
        raise RuntimeError(f"Unsupported platform: {system}")
    if not current_arch:
        raise RuntimeError(f"Unsupported architecture: {arch}")

    # Path to pre-built static library
    libs_dir = Path("libs")
    lib_path = libs_dir / current_platform / current_arch
    library_file = lib_path / "SynCache.a"

    # Check if library exists
    if not library_file.exists():
        # List available platforms for debugging
        available = []
        if libs_dir.exists():
            for plat in libs_dir.iterdir():
                if plat.is_dir():
                    for arc in plat.iterdir():
                        if arc.is_dir():
                            lib = arc / "SynCache.a"
                            if lib.exists():
                                available.append(f"{plat.name}/{arc.name}")

        raise RuntimeError(
            f"Static library not found for platform {current_platform}/{current_arch}.\n"
            f"Expected: {library_file}\n"
            f"Available platforms: {', '.join(available) if available else 'None'}"
        )

    print(f"Using static library: {library_file}")

    # Get pybind11 include path
    pybind11_include = get_pybind11_include()

    # Platform-specific compilation flags
    extra_compile_args = ["-std=c++17", "-O3"]
    extra_link_args = []
    extra_objects = [str(library_file)]
    libraries = []

    if current_platform == "windows":
        extra_compile_args += ["/EHsc", "/MD"]
        # Windows might need different library name
        if library_file.exists():
            extra_objects = [str(library_file)]
        else:
            # Try with .lib extension
            lib_file = lib_path / "SynCache.lib"
            if lib_file.exists():
                extra_objects = [str(lib_file)]

    elif current_platform == "macOS":
        # Try to detect minimum macOS version
        min_version = "11.0"  # Conservative default
        extra_compile_args += [
            f"-mmacosx-version-min={min_version}",
            "-arch", "arm64" if arch == "arm64" else "x86_64"
        ]
        extra_link_args += [
            f"-mmacosx-version-min={min_version}",
            "-arch", "arm64" if arch == "arm64" else "x86_64"
        ]

    else:  # linux
        extra_compile_args += ["-fPIC", "-pthread"]
        extra_link_args += ["-pthread", "-Wl,--no-undefined"]

    extension = Extension(
        name="SynCache._core",
        sources=["src/bindings.cpp"],
        include_dirs=[
            "include",
            pybind11_include,
        ],
        library_dirs=[str(lib_path)],
        libraries=libraries,
        extra_objects=extra_objects,
        language="c++",
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    )

    return extension


# Create package directory
Path("SynCache").mkdir(exist_ok=True)

# Create/update __init__.py
init_content = '''"""
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
'''

init_file = Path("SynCache/__init__.py")
if not init_file.exists() or init_file.read_text() != init_content:
    init_file.write_text(init_content)

# Get extension
try:
    extension = get_extension()
    ext_modules = [extension]
except Exception as e:
    print(f"Warning: Could not create extension: {e}")
    print("This is expected when running setup.py for metadata extraction.")
    print("The extension will be built during installation.")
    ext_modules = []

setup(
    name="pysyncache",
    version="1.0.4",
    packages=["SynCache"],
    ext_modules=ext_modules,
    python_requires=">=3.8",

    # Include all files needed for source build
    include_package_data=True,
    package_data={
        '': [
            'libs/**/*.a',
            'libs/**/*.lib',
            'include/**/*.h',
            'src/**/*.cpp',
        ],
    },

    # Metadata
    author="Waleed Shanaa",
    author_email="your.email@example.com",
    description="Python bindings for SynCache distributed caching system",
    long_description=open("README.md").read() if Path("README.md").exists() else "",
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pysyncache",
    license="MIT",

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: C++",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
    ],

    keywords=["cache", "distributed", "caching", "synapse", "performance"],

    # Helpful for users who have build issues
    setup_requires=[
        "pybind11>=2.6",
    ],
)