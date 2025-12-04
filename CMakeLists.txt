cmake_minimum_required(VERSION 3.15)
project(PySynCache)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if (WIN32)
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
endif ()

find_package(pybind11 REQUIRED)

# Build the pybind11 extension module
pybind11_add_module(PySynCache
    src/bindings.cpp
)

target_include_directories(PySynCache
    PRIVATE
        ${CMAKE_SOURCE_DIR}/include
)

# Detect platform and link correct static library
if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    if(CMAKE_SYSTEM_PROCESSOR STREQUAL "aarch64")
        set(LIB_PATH "${CMAKE_SOURCE_DIR}/libs/linux/arm64/SynCache.a")
    else()
        set(LIB_PATH "${CMAKE_SOURCE_DIR}/libs/linux/x64/SynCache.a")
    endif()
elseif(CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    if(CMAKE_SYSTEM_PROCESSOR STREQUAL "arm64")
        set(LIB_PATH "${CMAKE_SOURCE_DIR}/libs/macOS/arm64/SynCache.a")
    else()
        set(LIB_PATH "${CMAKE_SOURCE_DIR}/libs/macOS/x64/SynCache.a")
    endif()
elseif(CMAKE_SYSTEM_NAME STREQUAL "Windows")
    if(CMAKE_SYSTEM_PROCESSOR STREQUAL "ARM64")
        set(LIB_PATH "${CMAKE_SOURCE_DIR}/libs/windows/arm64/SynCache.a")
    else()
        set(LIB_PATH "${CMAKE_SOURCE_DIR}/libs/windows/x64/SynCache.a")
    endif()
endif()

if(EXISTS "${LIB_PATH}")
    message(STATUS "Linking with: ${LIB_PATH}")
    target_link_libraries(PySynCache PRIVATE "${LIB_PATH}")
else()
    message(FATAL_ERROR "Static library not found: ${LIB_PATH}")
endif()

# Optional static linking on Linux only (except Python)
if (UNIX AND NOT APPLE)
    target_link_options(PySynCache PRIVATE
        -static-libstdc++
        -static-libgcc
    )
endif()

if (WIN32)
    target_link_libraries(PySynCache PRIVATE
            ws2_32.lib
            crypt32.lib
            advapi32.lib
    )
endif ()
