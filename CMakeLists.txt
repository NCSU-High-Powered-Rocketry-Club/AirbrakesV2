cmake_minimum_required(VERSION 3.25)
project(${SKBUILD_PROJECT_NAME} LANGUAGES C)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)

file(GLOB_RECURSE AIRBRAKES_PY_FILES "${CMAKE_CURRENT_SOURCE_DIR}/airbrakes/*.py")

message(STATUS "cmake dir: ${CMAKE_CURRENT_SOURCE_DIR}")  # This is the root directory of the project
message(STATUS "skbuild dir: ${SKBUILD_PROJECT_NAME}")  # name of the project from pyproject.toml (airbrakes)
message(STATUS "binary dir: ${CMAKE_CURRENT_BINARY_DIR}")  # the build directory set in pyproject.toml (build/)
set(AIRBRAKES_DIR "${CMAKE_CURRENT_SOURCE_DIR}/airbrakes")  # The airbrakes package directory

foreach(py_file IN LISTS AIRBRAKES_PY_FILES)

  # Skip __init__.py files:
  if(py_file MATCHES "__init__.py$")
    continue()
  endif()

  message(STATUS "In loop for: ${py_file}")
  # Get relative path from project root (e.g. airbrakes/telemetry/logger.py)
  file(RELATIVE_PATH rel_path "${CMAKE_CURRENT_SOURCE_DIR}" "${py_file}")
  get_filename_component(dir_part "${rel_path}" DIRECTORY)  # Gets the directory (package) name (e.g. `airbrakes/telemetry`)
  get_filename_component(base_name "${rel_path}" NAME_WE)  # Gets the file name without extension (e.g. `logger`)

  # Generate output paths preserving directory structure
  # This will be the output C file (e.g. build/airbrakes/telemetry/logger.c)
  set(c_file_output_dir "${CMAKE_CURRENT_BINARY_DIR}/${dir_part}/${base_name}.c")
  message(STATUS "c_file_output_dir: ${c_file_output_dir}")

  add_custom_command(
    OUTPUT ${c_file_output_dir}
    COMMAND sh -c "uv run python -m cython '${py_file}' -3 --output-file '${c_file_output_dir}' -X boundscheck=false"
    DEPENDS ${py_file}
    COMMENT "Cythonizing ${rel_path}"
    VERBATIM
  )

  # In order to properly install the .so file, the target name needs to match the file name,
  # and the DESTINATION must be in the airbrakes/ directory. Note: Using ${CMAKE_SOURCE_DIR} will install the .so file in the root directory,
  # that works, but then the module isn't rebuilt automatically when the source file changes
  # That's why we just use the ${dir_part} variable to install the .so file in the correct directory,
  # which installs it in the .venv/lib/python3.x/site-packages/airbrakes/ directory.

  message(STATUS "Installing ${base_name} to ${dir_part}")
  python_add_library("${base_name}" MODULE ${c_file_output_dir} WITH_SOABI)
  
  # Install with original package structure
  install(TARGETS "${base_name}" DESTINATION "${dir_part}")
endforeach()

# old working code for one file:

# add_custom_command(
#   OUTPUT logger.c
#   COMMENT "Compiling ${CMAKE_CURRENT_SOURCE_DIR}/airbrakes/telemetry/logger.py"
#   COMMAND sh -c "uv run python -m cython '${CMAKE_CURRENT_SOURCE_DIR}/airbrakes/telemetry/logger.py' -3 --output-file '${CMAKE_CURRENT_BINARY_DIR}/logger.c'"
#   DEPENDS airbrakes/telemetry/logger.py
#   VERBATIM
# )

# python_add_library(logger MODULE logger.c WITH_SOABI)
# install(TARGETS logger DESTINATION ${SKBUILD_PROJECT_NAME}/telemetry)

