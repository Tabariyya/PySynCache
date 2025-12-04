from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import subprocess
import os
import sys
from pathlib import Path
import pybind11
import platform
import shutil

class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def run(self):

        for ext in self.extensions:
            self.build_cmake(ext)

    def build_cmake(self, ext):
        # Ensure we have cmake
        try:
            subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError("CMake must be installed to build this extension")

        extdir = os.path.abspath(
            os.path.dirname(self.get_ext_fullpath(ext.name))
        )

        # Build directory
        build_temp = os.path.join(self.build_temp, ext.name)
        if not os.path.exists(build_temp):
            os.makedirs(build_temp)

        pybind11_cmake = os.path.join(os.path.dirname(pybind11.__file__), 'share', 'cmake', 'pybind11')

        system = platform.system()

        # CMake configure
        cmake_args = [
            f'-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extdir}',
            f'-DPYTHON_EXECUTABLE={sys.executable}',
            f'-DCMAKE_BUILD_TYPE=Release',
            f'-DCMAKE_PREFIX_PATH={pybind11_cmake}',
        ]

        # Windows-specific CMake args
        if system == "Windows":
            cmake_args += [
                '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_RELEASE={}'.format(extdir),
                '-DCMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE={}'.format(extdir),
                '-A', 'x64' if sys.maxsize > 2 ** 32 else 'Win32'
            ]

        # Build args
        build_args = ['--config', 'Release']

        try:
            subprocess.check_call(
                ['cmake', ext.sourcedir] + cmake_args,
                cwd=build_temp,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
        except subprocess.CalledProcessError as e:
            print(f"CMake configure failed with error: {e}")
            raise

        # Build
        try:
            subprocess.check_call(
                ['cmake', '--build', '.'] + build_args,
                cwd=build_temp,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
        except subprocess.CalledProcessError as e:
            print(f"CMake build failed with error: {e}")
            raise

        # Platform-specific file extension
        system = platform.system()
        if system == "Windows":
            lib_ext = ".pyd"
        else:
            lib_ext = ".so"

        # Look for the output file with correct extension
        output_file = None
        for f in os.listdir(extdir):
            # Look for files starting with PySynCache and ending with the correct extension
            if f.startswith('PySynCache') and f.endswith(lib_ext):
                output_file = os.path.join(extdir, f)
                break

        # Also check for the target name directly
        target_name = os.path.join(extdir, '_core' + lib_ext)

        if output_file and os.path.exists(output_file):
            # Rename to _core with correct extension
            if os.path.exists(target_name):
                os.remove(target_name)  # Remove existing _core file if it exists

            shutil.move(output_file, target_name)
            print(f"Renamed {os.path.basename(output_file)} to _core{lib_ext}")
        else:
            # Check if CMake already produced _core directly
            for f in os.listdir(extdir):
                if f.startswith('_core') and f.endswith(lib_ext):
                    print(f"Found _core{lib_ext} directly from CMake build")
                    break
            else:
                print(f"Warning: Could not find output file with extension {lib_ext} in {extdir}")
                print(f"Files in directory: {os.listdir(extdir)}")


setup(
    name="pysyncache",
    version="1.0.4",
    packages=["SynCache"],
    ext_modules=[CMakeExtension('SynCache._core')],
    cmdclass={'build_ext': CMakeBuild},
    python_requires=">=3.7",
    zip_safe=False,

    setup_requires=["pybind11>=2.6"],

    author="Waleed Shanaa",
    author_email="waleed.shanaa@outlook.com",
    description="Python bindings for SynCache",
    long_description=open("README.md").read() if Path("README.md").exists() else "",
    long_description_content_type="text/markdown",
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
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Programming Language :: C++",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
    ],
)
