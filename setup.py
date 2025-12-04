from setuptools import setup, Extension
import platform
from pathlib import Path
import pybind11


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

    print(f"Using static library: {library_file}")

    pybind11_include = pybind11.get_include()
    print(f"Using pybind11: {pybind11_include}")

    # Platform-specific compilation flags
    extra_compile_args = ["-std=c++17", "-O3"]
    extra_link_args = []
    extra_objects = [str(library_file)]
    libraries = []

    if current_platform == "windows":
        extra_compile_args += ["/EHsc", "/MD"]
        extra_objects = [str(library_file)]

    elif current_platform == "linux":
        extra_compile_args += ["-fPIC", "-pthread"]
        extra_link_args += [
            "-pthread",
            "-Wl,--no-undefined",
            "-static-libstdc++",
            "-static-libgcc",
        ]

    return Extension(
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


setup(
    name="pysyncache",
    version="1.0.4",
    packages=["SynCache"],
    ext_modules=[get_extension()],
    python_requires=">=3.8",

    include_package_data=True,
    package_data={
        '': [
            'libs/**/*.a',
            'include/synCache/Controller.h',
            'src/bindings.cpp',
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