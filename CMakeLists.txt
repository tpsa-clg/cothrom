cmake_minimum_required(VERSION 3.16)

project(cothrom
  DESCRIPTION "Electoral redistricting via MCMC simulated annealing"
  LANGUAGES CXX)

# ---------------------------------------------------------------------------
# Build configuration
# ---------------------------------------------------------------------------
# The compiler is NOT hardcoded. Select it the standard CMake way, e.g.
#   cmake -B build -DCMAKE_CXX_COMPILER=CC       # LUMI / Cray wrapper
#   cmake -B build -DCMAKE_CXX_COMPILER=clang++
#   CXX=g++ cmake -B build
# Optimisation level is controlled by CMAKE_BUILD_TYPE (default: Release).

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Release CACHE STRING
      "Build type (Debug, Release, RelWithDebInfo, MinSizeRel)" FORCE)
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------
find_package(OpenMP REQUIRED)

# std::filesystem needs an extra library on some older GCC toolchains (< 9).
# On modern compilers this target does not exist and is simply skipped.
set(FS_LIB "")
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU" AND CMAKE_CXX_COMPILER_VERSION VERSION_LESS 9.0)
  set(FS_LIB stdc++fs)
endif()

# ---------------------------------------------------------------------------
# Core library (Map + statistics helpers, shared by both executables)
# ---------------------------------------------------------------------------
add_library(cothrom_core STATIC
  src/Map.cpp
  src/statfuncs.cpp)

target_include_directories(cothrom_core
  PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/headers)

target_link_libraries(cothrom_core
  PUBLIC OpenMP::OpenMP_CXX m)

# ---------------------------------------------------------------------------
# Executables
# ---------------------------------------------------------------------------
add_executable(MCMC_SA src/MCMC_SA.cpp)
target_link_libraries(MCMC_SA PRIVATE cothrom_core ${FS_LIB})

add_executable(actual_H src/actual_H.cpp)
target_link_libraries(actual_H PRIVATE cothrom_core ${FS_LIB})
