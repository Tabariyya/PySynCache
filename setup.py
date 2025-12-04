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

        # Build args
        build_args = ['--config', 'Release']

        if system == "Windows":
            build_args += ['--', '/m']
        else:
            build_args += ['--', '-j2']

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

        # Rename output to match Python expectations
        output_file = None
        for f in os.listdir(extdir):
            if f.startswith('PySynCache') and (f.endswith('.so') or f.endswith('.pyd')):
                output_file = os.path.join(extdir, f)
                break

        if output_file and os.path.exists(output_file):
            target_name = os.path.join(extdir, '_core' + os.path.splitext(output_file)[1])
            shutil.move(output_file, target_name)
            print(f"Renamed {os.path.basename(output_file)} to _core{os.path.splitext(output_file)[1]}")


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
