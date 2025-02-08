cmake_minimum_required(VERSION 3.25)
project(${SKBUILD_PROJECT_NAME} LANGUAGES C)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)

add_custom_command(
  OUTPUT logger.c
  COMMENT "Compiling ${CMAKE_CURRENT_SOURCE_DIR}/airbrakes/telemetry/logger.py"
  COMMAND sh -c "uv run python -m cython '${CMAKE_CURRENT_SOURCE_DIR}/airbrakes/telemetry/logger.py' -3 --output-file '${CMAKE_CURRENT_BINARY_DIR}/logger.c'"
  DEPENDS airbrakes/telemetry/logger.py
  VERBATIM
)

python_add_library(logger MODULE logger.c WITH_SOABI)
install(TARGETS logger DESTINATION ${SKBUILD_PROJECT_NAME}/telemetry)
