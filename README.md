# SynCache-Python

🚀 **Distributed Caching Made Simple** - Local speed with distributed scale!

SynCache is a revolutionary caching library that combines the speed of local caching with the scalability of distributed systems. Data is cached locally on each machine for blazing-fast access (no TCP overhead!), while a background broker automatically synchronizes caches across all instances.

## ✨ Key Features

- **Lightning Fast** - Local machine caching means no network latency
- **Horizontally Scalable** - Broker-based background synchronization keeps all instances in sync
- **Simple API** - Intuitive decorators for easy integration
- **Multi-Language Support** - Python bindings with C++ core
- **Type-Safe** - Full type hint support and automatic serialization
- **Flexible TTL** - Per-entry time-to-live configuration

## 📦 Installation

```bash
pip install synccache-python