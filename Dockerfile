FROM python:3.13-slim AS builder

RUN pip install setuptools pybind11

# Work directory
WORKDIR /app

# Copy your project
COPY include include
COPY libs libs
COPY src src
COPY SynCache SynCache
COPY setup.py setup.py
COPY README.md README.md
COPY pyproject.toml pyproject.toml
COPY CMakeLists.txt CMakeLists.txt
COPY MANIFEST.in MANIFEST.in


RUN python setup.py sdist

FROM python:3.14-slim AS tester

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    cmake \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app

COPY --from=builder /app/dist/pysyncache*/ pysyncache.tar.gz
RUN pip install pysyncache.tar.gz


COPY tests tests
WORKDIR /app/tests
RUN python -m unittest -v

from alpine:latest as exporter
COPY --from=tester /app/pysyncache.tar.gz pysyncache.tar.gz

