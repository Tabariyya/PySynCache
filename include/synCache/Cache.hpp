#pragma once

#include <memory>
#include <optional>
#include <string>
#include <vector>

class Cache {
    struct Impl;
    std::unique_ptr<Impl> impl;

    Cache();

public:
    ~Cache();

    Cache(const Cache &) = delete;

    Cache &operator=(const Cache &) = delete;

    static void initialize(const std::string &brokerAuthToken, long maxNoOfEntries);

    static Cache &getInstance();

    void set(const std::string &nameSpace,
             const std::string &id,
             const std::string &value,
             const std::optional<long> &ttl) const;

    void set(const std::string &nameSpace,
             const std::string &id,
             const std::vector<uint8_t> &value,
             const std::optional<long> &ttl) const;

    void set(const std::string &nameSpace,
             const std::string &id,
             std::vector<uint8_t> &&value,
             const std::optional<long> &ttl) const;

    std::shared_ptr<const std::vector<uint8_t>> getRaw(const std::string &nameSpace, const std::string &id) const;

    std::optional<std::string> getAsString(const std::string &nameSpace, const std::string &id) const;

    void evict(const std::string &nameSpace, const std::string &id) const;

    void evict() const;

    void evict(const std::string &nameSpace) const;
};
