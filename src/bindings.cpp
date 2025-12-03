#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
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

        // Use lambda wrappers for overloaded methods
        .def("set_string", [](const Controller& c,
                              const std::string& ns,
                              const std::string& id,
                              const std::string& val,
                              const std::optional<std::time_t>& ttl) {
            c.set(ns, id, val, ttl);
        }, py::arg("namespace"), py::arg("id"), py::arg("value"), py::arg("ttl") = py::none())

        .def("set_bytes", [](const Controller& c,
                             const std::string& ns,
                             const std::string& id,
                             const std::vector<uint8_t>& val,
                             const std::optional<std::time_t>& ttl) {
            c.set(ns, id, val, ttl);
        }, py::arg("namespace"), py::arg("id"), py::arg("value"), py::arg("ttl") = py::none())

        .def("get_raw", &Controller::getRaw,
             py::arg("namespace"), py::arg("id"))

        .def("get_as_string", &Controller::getAsString,
             py::arg("namespace"), py::arg("id"))

        .def("evict", &Controller::evict,
             py::arg("namespace"), py::arg("id"))

        .def("evict_namespace", [](const Controller& c, const std::string& ns) {
            c.evictAll(ns);
        }, py::arg("namespace"))

        .def("evict_all", [](const Controller& c) {
            c.evictAll();
        })

        .def("__repr__", [](const Controller&) {
            return "<SynCache.Controller>";
        });
}