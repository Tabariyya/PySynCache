from setuptools import setup, Extension, find_packages
import platform
from pathlib import Path
import sys
import subprocess
import os


def get_pybind11_include():
    try:
        import pybind11
        return pybind11.get_include()
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pybind11"])
        import pybind11
        return pybind11.get_include()


# Get current platform
system = platform.system().lower()
arch = platform.machine().lower()

print(f"Building on: {system}/{arch}")

platform_map = {
    'linux': 'linux',
    'darwin': 'macOS',
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

print(f"Using platform: {current_platform}/{current_arch}")

# Path to pre-built static library
libs_dir = Path("libs")
lib_path = libs_dir / current_platform / current_arch
library_file = lib_path / "SynCache.a"

# Verify library exists
if not library_file.exists():
    raise FileNotFoundError(f"Library not found: {library_file}")

print(f"Using library: {library_file}")

# Get pybind11 include path
pybind11_include = get_pybind11_include()
print(f"Pybind11 include: {pybind11_include}")

# Platform-specific compilation flags
extra_compile_args = ["-std=c++17", "-O3"]
extra_link_args = []
extra_objects = [str(library_file)]
libraries = []

if current_platform == "windows":
    extra_compile_args += ["/EHsc", "/MD"]

elif current_platform == "macOS":
    # CRITICAL: Match the macOS version your library was built for
    # macOS 26.0 is Sequoia (version 15.0)
    # Use 15.0 as minimum deployment target for compatibility
    extra_compile_args += [
        "-mmacosx-version-min=15.0",  # Changed from 10.15 to 15.0
        "-arch", "arm64",
    ]
    extra_link_args += [
        "-mmacosx-version-min=15.0",  # Changed from 10.15 to 15.0
        "-arch", "arm64",
    ]

    # Also override Python's default deployment target
    os.environ['MACOSX_DEPLOYMENT_TARGET'] = "15.0"

    # Check Python's deployment target
    import sysconfig

    print(f"Python deployment target: {sysconfig.get_config_var('MACOSX_DEPLOYMENT_TARGET')}")

else:  # linux
    extra_compile_args += ["-fPIC", "-pthread"]
    extra_link_args += ["-pthread", "-Wl,--no-undefined"]

# Create package directory
package_dir = Path("SynCache")
package_dir.mkdir(exist_ok=True)

# Define the C++ extension
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

# macOS specific build options
cmdclass = {}
if current_platform == "macOS":
    from distutils.command.build_ext import build_ext


    class MacOSBuildExt(build_ext):
        def build_extensions(self):
            # Override deployment target
            self.compiler.macosx_deployment_target = "15.0"

            # Update compiler flags
            for ext in self.extensions:
                ext.extra_compile_args = [
                    arg.replace("10.15", "15.0")
                    if isinstance(arg, str) else arg
                    for arg in ext.extra_compile_args
                ]
                ext.extra_link_args = [
                    arg.replace("10.15", "15.0")
                    if isinstance(arg, str) else arg
                    for arg in ext.extra_link_args
                ]

            super().build_extensions()


    cmdclass['build_ext'] = MacOSBuildExt

setup(
    name="PySynCache",
    version="1.0.0",
    packages=["SynCache"],
    ext_modules=[extension],
    python_requires=">=3.8",

    # macOS deployment target
    options={
        'build_ext': {
            'plat_name': 'macosx-15.0-arm64',  # Updated to 15.0
        }
    },

    cmdclass=cmdclass,

    author="Waleed Shanaa",
    description="Python bindings for SynCache",
)