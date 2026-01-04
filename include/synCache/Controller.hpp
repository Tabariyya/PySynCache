#pragma once

#include <memory>
#include <optional>
#include <string>
#include <vector>

class Controller {
    struct Impl;
    std::unique_ptr<Impl> impl;

public:
    explicit Controller(const std::string &BrokerURL, const std::string &brokerAuthToken, long maxNoOfEntries);

    ~Controller();

    void set(const std::string &nameSpace,
             const std::string &id,
             const std::string &value,
             const std::optional<long> &ttl) const;

    void set(const std::string &nameSpace,
             const std::string &id,
             const std::vector<uint8_t> &value,
             const std::optional<long> &ttl) const;

    std::optional<std::vector<uint8_t> > getRaw(const std::string &nameSpace, const std::string &id) const;

    std::optional<std::string> getAsString(const std::string &nameSpace, const std::string &id) const;

    void evict(const std::string &nameSpace, const std::string &id) const;

    void evictAll() const;

    void evictAll(const std::string &nameSpace) const;
};
