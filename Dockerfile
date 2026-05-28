FROM python:3.13-slim AS builder

RUN pip install --no-cache-dir setuptools wheel pybind11 build

WORKDIR /app

COPY include include
COPY libs libs
COPY src src
COPY SynCache SynCache
COPY setup.py setup.py
COPY README.md README.md
COPY pyproject.toml pyproject.toml
COPY CMakeLists.txt CMakeLists.txt
COPY MANIFEST.in MANIFEST.in

RUN python -m build --sdist

FROM python:3.13-slim AS tester

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential g++ cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/dist /app/dist
RUN pip install /app/dist/pysyncache-*.tar.gz

ARG BROKER_TOKEN
ENV BROKER_TOKEN=${BROKER_TOKEN}

COPY tests tests
RUN python -m unittest discover -v tests/

FROM python:3.13-slim AS publisher

RUN pip install --no-cache-dir twine

COPY --from=builder /app/dist /dist
