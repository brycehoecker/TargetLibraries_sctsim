# Specify the minimum version of CMake required to build the project
cmake_minimum_required(VERSION 3.20 FATAL_ERROR)

# Set the project name and version
project(TargetDriver)
set(TargetDriver_VERSION_MAJOR 1)
set(TargetDriver_VERSION_MINOR 0)

# Options to enable or disable building of the Python wrapper and unit tests, and to turn compiler warnings on or off
option(PYTHON "Build the Python wrapper" ON)
option(UNITTEST "Enable unit test" ON)
option(COMPILER_WARNINGS "Turn compiler warnings on" ON)

# Check for the existence of the 'rt' library and the 'clock_gettime' function
include(CheckLibraryExists)
check_library_exists(rt clock_gettime "time.h" HAVE_CLOCK_GETTIME)
if (HAVE_CLOCK_GETTIME)
  list(APPEND EXTLIBS rt)   # Append 'rt' library to EXTLIBS if it exists
endif()

# Set the default optimization level for the compiler
set(OPTIMIZATION_LEVEL "-O0" CACHE STRING "Set the optimization level")

# Locate source files for the core library in the specified directory
aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/src SOURCES)
# Create a shared library from the located source files
add_library(TargetDriver SHARED ${SOURCES})

# Set compiler options based on the compiler being used (Clang, AppleClang, or GNU)
if("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang" OR "${CMAKE_CXX_COMPILER_ID}" STREQUAL "AppleClang")
  target_compile_options(TargetDriver PUBLIC -std=c++20 -stdlib=libc++ ${OPTIMIZATION_LEVEL})
elseif("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU")
  if(CMAKE_CXX_COMPILER_VERSION VERSION_LESS 11.4)
    message(FATAL_ERROR "GCC version must be at least 11.4. Found version ${CMAKE_CXX_COMPILER_VERSION}.")
  endif()
  target_compile_options(TargetDriver PUBLIC -std=c++20 ${OPTIMIZATION_LEVEL})
endif()

# Set general compiler options for all compilers
target_compile_options(TargetDriver PUBLIC -Wall)

# Set additional compiler warnings based on the COMPILER_WARNINGS option
if(COMPILER_WARNINGS)
    target_compile_options(TargetDriver PUBLIC -Wextra -Wconversion)
endif()

# Set include directories for the target
target_include_directories (TargetDriver
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# Link the target with external libraries specified in EXTLIBS
target_link_libraries(TargetDriver PUBLIC ${EXTLIBS})

# Add preprocessor definitions to the target
target_compile_definitions (TargetDriver
  PUBLIC
    TARGETDRIVER_VERSION="${TargetDriver_VERSION_MAJOR}.${TargetDriver_VERSION_MINOR}"
    TARGET_BUILD_PATH="${CMAKE_BINARY_DIR}"
    TARGET_INSTALL_PATH="${CMAKE_INSTALL_PREFIX}"
)

# Set properties for the shared library versioning
set_target_properties (TargetDriver
  PROPERTIES 
    SOVERSION "${TargetDriver_VERSION_MAJOR}.${TargetDriver_VERSION_MINOR}"
    VERSION "${TargetDriver_VERSION_MAJOR}.${TargetDriver_VERSION_MINOR}"
)

# Installation rules for the library and its headers
install(TARGETS TargetDriver EXPORT ${PROJECT_NAME}Config LIBRARY DESTINATION lib)
install(DIRECTORY ${PROJECT_SOURCE_DIR}/include/ DESTINATION include)

# Make the project importable from build and install locations
include (CMakePackageConfigHelpers)
write_basic_package_version_file(
  "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}ConfigVersion.cmake"
  VERSION ${TargetDriver_VERSION_MAJOR}
  COMPATIBILITY AnyNewerVersion
)
export(EXPORT ${PROJECT_NAME}Config FILE ${PROJECT_NAME}Config.cmake)
set(_config_dir share/${PROJECT_NAME})
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}ConfigVersion.cmake"
  DESTINATION ${_config_dir}
)
install(EXPORT ${PROJECT_NAME}Config
  DESTINATION ${_config_dir}
)

# Copy configuration files into the build directory
file(GLOB CONFIG_FILES "${CMAKE_CURRENT_SOURCE_DIR}/config/*")
file(COPY ${CONFIG_FILES} DESTINATION ${CMAKE_BINARY_DIR}/share/${PROJECT_NAME}/config/) 

# Installation rules for configuration files
install(DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/config" DESTINATION share/${PROJECT_NAME}/)

#------------------------------------------------------------------------------
# Tools
#------------------------------------------------------------------------------

# Set the output directory for runtime executables
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

## OLD List of executable names to be built
#SET(EXE_NAMES tester testerT7 testerT7BP testerTC generate_markdown_files testbuffer update_firmware)

# NEW List of executable names to be built
SET(EXE_NAMES tester testerTECT5TEA generate_markdown_files testbuffer update_firmware)

# Append 'pthread' to the list of external libraries
list(APPEND EXTLIBS pthread)

# Loop to add each executable, link it with libraries, and set installation rules
foreach(EXE_NAME ${EXE_NAMES})
    add_executable(${EXE_NAME} ${CMAKE_CURRENT_SOURCE_DIR}/src_exe/${EXE_NAME}.cc)
    target_link_libraries(${EXE_NAME} TargetDriver ${EXTLIBS})
endforeach()
install(TARGETS ${EXE_NAMES} RUNTIME DESTINATION bin)

#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------
# Placeholder for future tests (currently no tests defined)

#------------------------------------------------------------------------------
# Python bindings
#------------------------------------------------------------------------------
# Section for adding Python bindings if enabled
if(PYTHON)
    # Find Python executable
    FIND_PROGRAM(PYTHON_EXECUTABLE python PATHS ENV PATH NO_DEFAULT_PATH)
    
    # If Python is found, proceed with Python bindings
    if(PYTHON_EXECUTABLE)
        message(STATUS "Found python")
        find_package(SWIG REQUIRED)

        # Include SWIG use file
        include(${SWIG_USE_FILE})

        # Find Python and NumPy include directories
        execute_process(COMMAND python -c "import numpy; print(numpy.get_include())" OUTPUT_VARIABLE NUMPY_INCLUDE_DIR OUTPUT_STRIP_TRAILING_WHITESPACE)
        execute_process(COMMAND python -c "from distutils import sysconfig; print(sysconfig.get_python_inc())" OUTPUT_VARIABLE PYTHON_INCLUDE_DIRS OUTPUT_STRIP_TRAILING_WHITESPACE)
  
        # Include directories for SWIG
        include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include ${NUMPY_INCLUDE_DIR} ${PYTHON_INCLUDE_DIRS})

        # Compile options for SWIG
        get_property(TargetDriver_COMPILE_OPTIONS TARGET TargetDriver PROPERTY INTERFACE_COMPILE_OPTIONS)
        string(REPLACE ";" " " TargetDriver_COMPILE_OPTIONS_STR "${TargetDriver_COMPILE_OPTIONS}")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D__STDC_FORMAT_MACROS  ${TargetDriver_COMPILE_OPTIONS_STR}")

        # Set source file properties for SWIG
        set_source_files_properties(target_driver.i PROPERTIES CPLUSPLUS ON)

        # Add SWIG library
        swig_add_library(target_driver LANGUAGE python SOURCES target_driver.i ${SOURCES})
        get_directory_property(OutputTargets DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} BUILDSYSTEM_TARGETS)
        message(STATUS "Targets in directory: ${OutputTargets}")

        # Linker flags for OSX
        if(APPLE)
            SET_TARGET_PROPERTIES(target_driver PROPERTIES LINK_FLAGS "-undefined dynamic_lookup")
        endif(APPLE)

    # Compile definitions for SWIG target
    target_compile_definitions(target_driver
        PUBLIC
        TARGETDRIVER_VERSION="${TargetDriver_VERSION_MAJOR}.${TargetDriver_VERSION_MINOR}"
        TARGET_BUILD_PATH="${CMAKE_BINARY_DIR}"
        TARGET_INSTALL_PATH="${CMAKE_INSTALL_PREFIX}"
    )

    # Link SWIG library with Python libraries and external libraries
    swig_link_libraries(target_driver ${PYTHON_LIBRARIES} ${EXTLIBS})

    # Find Python site-packages directory
    set(PYTHON_SITE_PACKAGES "")
    execute_process(COMMAND python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())" OUTPUT_VARIABLE PYTHON_SITE_PACKAGES OUTPUT_STRIP_TRAILING_WHITESPACE)

    # Installation rules for SWIG-generated Python files
    install(TARGETS target_driver DESTINATION ${PYTHON_SITE_PACKAGES})
    install(FILES ${PROJECT_BINARY_DIR}/target_driver.py DESTINATION ${PYTHON_SITE_PACKAGES} COMPONENT pylibrary)
    message(STATUS "Python support is added")
endif(PYTHON_EXECUTABLE)
endif(PYTHON)
