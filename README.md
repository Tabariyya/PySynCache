# PySynCache

Python bindings for [SynCache](https://syncache.tabariyya.com) — an in-process distributed cache that stores data directly in your application's heap memory while keeping every instance in the cluster automatically in sync.

[![PyPI version](https://img.shields.io/pypi/v/pysyncache)](https://pypi.org/project/pysyncache/)
[![Python](https://img.shields.io/pypi/pyversions/pysyncache)](https://pypi.org/project/pysyncache/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

---

## Why SynCache?

Traditional distributed caches (Redis, Memcached) require a network round-trip on every read. SynCache eliminates that entirely — reads come straight from the same heap your application runs in, with no kernel syscalls or context switches.

| Operation | SynCache | Traditional Remote Cache |
|-----------|----------|--------------------------|
| Read      | **197× faster** | baseline |
| Write     | **8× faster**   | baseline |
| Eviction  | **18× faster**  | baseline |

Writes still sync across the cluster through a lightweight broker, so every instance stays consistent without you managing any pub/sub logic.

---

## How It Works

```
  Instance A          Instance B          Instance C
 ┌──────────┐        ┌──────────┐        ┌──────────┐
 │ In-proc  │        │ In-proc  │        │ In-proc  │
 │  Cache   │        │  Cache   │        │  Cache   │
 └────┬─────┘        └────┬─────┘        └────┬─────┘
      │                   │                   │
      └───────────────────┼───────────────────┘
                          │
                  ┌───────┴────────┐
                  │ SynCache Broker │
                  └────────────────┘
```

- **Reads** bypass the broker entirely — served directly from process memory
- **Writes** propagate through the broker to all instances using the affected namespace
- **Evictions** broadcast cluster-wide automatically

---

## Installation

```bash
pip install pysyncache
```

Requires Python 3.7+. Supported on Linux, macOS, and Windows (x64 and arm64).

---

## Getting a Token

SynCache requires a broker token to connect your instances.

1. Visit [syncache.tabariyya.com](https://syncache.tabariyya.com)
2. Submit your name, email, and project name
3. Receive your token instantly via email
4. Store it as an environment variable:

```bash
export SYNCACHE_TOKEN=your_token_here
```

The free tier supports up to **5 connected instances** with full API access. No credit card required.

---

## Quick Start

```python
import os
from SynCache import Cache

# Initialize once at application startup
Cache.initialize(
    broker_auth_token=os.getenv("SYNCACHE_TOKEN"),
    max_entries=1000
)

# Store a value (syncs to all instances)
Cache.set("users", "user:1", {"name": "Alice", "role": "admin"})

# Read directly from local memory (no network)
user = Cache.get("users", "user:1")

# Evict a single entry across the cluster
Cache.evict("users", "user:1")

# Evict an entire namespace across the cluster
Cache.evict_all("users")
```

---

## Decorators

PySynCache ships with decorators that mirror the familiar `@Cacheable` / `@CachePut` / `@CacheEvict` pattern.

```python
from SynCache.decorators import Cacheable, CachePut, CacheEvict

@Cacheable(namespace="users", ttl=60)
def get_user(user_id: str) -> dict:
    # Only called on a cache miss — result cached automatically
    return db.fetch_user(user_id)

@CachePut(namespace="users")
def update_user(user_id: str, data: dict) -> dict:
    # Result written to cache and synced across the cluster
    return db.update_user(user_id, data)

@CacheEvict(namespace="users")
def delete_user(user_id: str) -> None:
    # Entry evicted from all instances on return
    db.delete_user(user_id)
```

---

## Configuration

| Parameter | Type | Description |
|-----------|------|-------------|
| `broker_auth_token` | `str` | Token from your SynCache account |
| `max_entries` | `int` | Maximum number of entries held in process memory |

TTL (time-to-live) is configured per entry in seconds. Entries without a TTL persist until evicted.

---

## Consistency Model

| Scenario | Behaviour |
|----------|-----------|
| Local read after local write | Strong consistency — immediately visible |
| Cross-instance propagation | Eventual consistency with sub-millisecond sync |
| Namespace scoping | Updates only reach instances actively using that namespace |

---

## Links

- **Website & docs**: [syncache.tabariyya.com](https://syncache.tabariyya.com)
- **GitHub**: [github.com/Tabariyya/PySynCache](https://github.com/Tabariyya/PySynCache)
- **Issues**: [github.com/Tabariyya/PySynCache/issues](https://github.com/Tabariyya/PySynCache/issues)
- **PyPI**: [pypi.org/project/pysyncache](https://pypi.org/project/pysyncache/)
