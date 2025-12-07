#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include "synCache/Controller.h"

namespace py = pybind11;

PYBIND11_MODULE(_core, m) {
    m.doc() = "SynCache Python bindings";

    // Bind Controller class
    py::class_<Controller>(m, "Controller")
        .def(py::init<const std::string&, const std::string&, long>(),
             py::arg("broker_url"),
             py::arg("broker_auth_token"),
             py::arg("max_entries"))

        .def("set", [](const Controller& c,
                             const std::string& ns,
                             const std::string& id,
                             const py::bytes& val,
                             const std::optional<long>& ttl) {
            // Extract bytes to vector<uint8_t>
            char* buffer;
            py::ssize_t length;
            if (PyBytes_AsStringAndSize(val.ptr(), &buffer, &length) != 0) {
                throw py::error_already_set();
            }
            std::vector<uint8_t> vec(buffer, buffer + length);
            c.set(ns, id, vec, ttl);
        }, py::arg("namespace"), py::arg("id"), py::arg("value"), py::arg("ttl") = py::none())

        .def("get", [](const Controller& c, const std::string& ns, const std::string& id) -> py::object {
            auto result = c.getRaw(ns, id);
            if (result.has_value()) {
                // Convert vector<uint8_t> to Python bytes
                const auto& vec = result.value();
                return py::bytes(reinterpret_cast<const char*>(vec.data()), vec.size());
            }
            return py::none();
        }, py::arg("namespace"), py::arg("id"))


        .def("evict", &Controller::evict,
             py::arg("namespace"), py::arg("id"))

        .def("evict_all", [](const Controller& c) {
            c.evictAll();
        })

        .def("evict_namespace", [](const Controller& c, const std::string& ns) {
            c.evictAll(ns);
        }, py::arg("namespace"))

        .def("__repr__", [](const Controller&) {
            return "<SynCache.Controller>";
        });
}