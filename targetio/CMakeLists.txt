cmake_minimum_required(VERSION 3.0 FATAL_ERROR)

# Project name
project(TargetIO)
set(TARGET_IO_VERSION_MAJOR 1)
set(TARGET_IO_VERSION_MINOR 0)
set(CMAKE_VERBOSE_MAKEFILE OFF)

option(PYTHON "Build the Python wrapper" ON)
option(NUMPY "Enable returning NumPy arrays in a few methods" ON)
option(UNITTEST "Enable unit test" OFF)
option(COMPILER_WARNINGS "Turn compiler warnings on" OFF)

if(TARGET TargetDriver)
    message(STATUS "Building against bundle TargetDriver")
else()
    find_package(TargetDriver REQUIRED ${CMAKE_SOURCE_DIR})
endif()

# Set the path to find FindCFITSIO.cmake
# Occurs after TargetDriver inclusion to make sure usr/local/include is not
# prioritised for the TargetDriver headers
if(CMAKE_INSTALL_PREFIX)
   set(CMAKE_PREFIX_PATH ${CMAKE_INSTALL_PREFIX})
endif(CMAKE_INSTALL_PREFIX)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${CMAKE_CURRENT_SOURCE_DIR}/misc)
find_package(CFITSIO REQUIRED)
list(APPEND EXTLIBS ${CFITSIO_LIBRARIES})

#------------------------------------------------------------------------------
# Setup library compilation and installation
#------------------------------------------------------------------------------
if(APPLE)
  # This option must be enabled to fix issue #11998
  # https://forge.in2p3.fr/issues/11998
  set(CMAKE_MACOSX_RPATH TRUE)
endif(APPLE)
if((APPLE) OR (EXISTS $ENV{CONDA_PREFIX}))
  # The following settings were copied from
  # https://cmake.org/Wiki/CMake_RPATH_handling
  # to avoid the rpath issue (issue #11998) that appears on OS X El Capitan
  # https://forge.in2p3.fr/issues/11998

  # use, i.e. don't skip the full RPATH for the build tree
  set(CMAKE_SKIP_BUILD_RPATH  FALSE)

  # when building, don't use the install RPATH already
  # (but later on when installing)
  set(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE) # Changed to TRUE by A.O.

  set(CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib")

  # add the automatically determined parts of the RPATH
  # which point to directories outside the build tree to the install RPATH
  set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
endif()

if(APPLE)
  #the RPATH to be used when installing, but only if it's not a system directory
  list(FIND CMAKE_PLATFORM_IMPLICIT_LINK_DIRECTORIES "${CMAKE_INSTALL_PREFIX}/lib" isSystemDir)
  if("${isSystemDir}" STREQUAL "-1")
    set(CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib")
  endif("${isSystemDir}" STREQUAL "-1")
endif(APPLE)

# include_directories(BEFORE ${CMAKE_CURRENT_SOURCE_DIR}/include)
aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/src SOURCES)
add_library(TargetIO SHARED ${SOURCES})

#Set compiler options
if("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang" OR "${CMAKE_CXX_COMPILER_ID}" STREQUAL "AppleClang")
  target_compile_options(TargetIO PUBLIC -std=c++11 -stdlib=libc++)
elseif("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU")
  execute_process(COMMAND ${CMAKE_C_COMPILER} -dumpversion OUTPUT_VARIABLE GCC_VERSION)
  if(GCC_VERSION VERSION_GREATER 4.7 OR GCC_VERSION VERSION_EQUAL 4.7)
    target_compile_options(TargetIO PUBLIC -std=c++11)
  else()
    target_compile_options(TargetIO PUBLIC -std=c++0x)
  endif()
endif()
target_compile_options(TargetIO PUBLIC -O2 -Wall)

#Set compiler warnings
if(COMPILER_WARNINGS)
    target_compile_options(TargetIO PUBLIC -Wextra -Wconversion)
endif()


target_include_directories (TargetIO
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
    ${CFITSIO_INCLUDE_DIRS}
)

target_link_libraries(TargetIO ${EXTLIBS} TargetDriver)

target_compile_definitions (TargetIO
  PUBLIC
    TARGET_IO_VERSION="${TARGET_IO_VERSION_MAJOR}.${TARGET_IO_VERSION_MINOR}"
)

set_target_properties (TargetIO
  PROPERTIES 
    SOVERSION "${TARGET_IO_VERSION_MAJOR}.${TARGET_IO_VERSION_MINOR}"
    VERSION "${TARGET_IO_VERSION_MAJOR}.${TARGET_IO_VERSION_MINOR}"
)


install (TARGETS TargetIO EXPORT ${PROJECT_NAME}Config LIBRARY DESTINATION lib)
install (DIRECTORY ${PROJECT_SOURCE_DIR}/include/ DESTINATION include)


# -----------------------------------------------------------------------------
# Export targets for use in downstream CMake projects
# -----------------------------------------------------------------------------
include ( CMakePackageConfigHelpers )
# Make importable from build directory
write_basic_package_version_file(
  "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}ConfigVersion.cmake"
  VERSION ${TARGET_IO_VERSION_MAJOR}.${TARGET_IO_VERSION_MINOR}
  COMPATIBILITY AnyNewerVersion
)
export(EXPORT ${PROJECT_NAME}Config FILE ${PROJECT_NAME}Config.cmake)

# Make importable from install location
set(_config_dir share/${PROJECT_NAME})
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}ConfigVersion.cmake"
  DESTINATION ${_config_dir}
)
install(EXPORT ${PROJECT_NAME}Config
  DESTINATION ${_config_dir}
)


#------------------------------------------------------------------------------
# Tools
#------------------------------------------------------------------------------
set(
    CMAKE_RUNTIME_OUTPUT_DIRECTORY
    ${CMAKE_BINARY_DIR}/bin
    )

SET(EXE_NAMES readCHEC-M CHECDataListener)

list(APPEND EXTLIBS pthread)
foreach(EXE_NAME ${EXE_NAMES})
  add_executable(${EXE_NAME} ${CMAKE_CURRENT_SOURCE_DIR}/examples/${EXE_NAME}.cc)
  target_include_directories (${EXE_NAME} PRIVATE ${CFITSIO_INCLUDE_DIRS})
  target_link_libraries(${EXE_NAME} TargetDriver TargetIO ${EXTLIBS})
endforeach()
install(TARGETS ${EXE_NAME} RUNTIME DESTINATION bin)

#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------
if(UNITTEST)
  
  # Find the Boost unit test framework
  find_package(Boost COMPONENTS unit_test_framework REQUIRED)
  ADD_DEFINITIONS(-DBOOST_ALL_DYN_LINK)
  list(APPEND EXTLIBS ${Boost_LIBRARIES})

  enable_testing()
  aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/test TEST_NAMES)
  foreach(TEST_NAME ${TEST_NAMES})
    get_filename_component(TEST_NAME ${TEST_NAME} NAME_WE)
    add_executable(${TEST_NAME} ${CMAKE_CURRENT_SOURCE_DIR}/test/${TEST_NAME}.cc)
    add_test(NAME ${TEST_NAME} COMMAND ${TEST_NAME})
    target_include_directories(${TEST_NAME} PRIVATE ${CFITSIO_INCLUDE_DIRS} ${Boost_INCLUDE_DIRS})
    list(APPEND TEST_EXE_NAMES ${TEST_NAME})
    target_link_libraries(${TEST_NAME} TargetIO TargetDriver ${EXTLIBS})
  endforeach()
  message(STATUS "Unit tests is added")
endif(UNITTEST)

#------------------------------------------------------------------------------
# Python Bindings
#------------------------------------------------------------------------------
if(PYTHON)
  #check if there is a python interpreter to begin with  
  FIND_PROGRAM(PYTHON_EXECUTABLE python
      PATHS ENV PATH         # look in the PATH environment variable
      NO_DEFAULT_PATH        # do not look anywhere else...
      )

  if(PYTHON_EXECUTABLE)
    message(STATUS "Found python")
    find_package(SWIG REQUIRED)
    include(${SWIG_USE_FILE})
    #A more robust way of finding the correct python version and it's include directories
    execute_process(COMMAND python -c "import numpy; print(numpy.get_include())" OUTPUT_VARIABLE NUMPY_INCLUDE_DIR OUTPUT_STRIP_TRAILING_WHITESPACE)
    execute_process(COMMAND python -c 
                    "from distutils import sysconfig; print(sysconfig.get_python_inc())" 
                    OUTPUT_VARIABLE PYTHON_INCLUDE_DIRS 
                    OUTPUT_STRIP_TRAILING_WHITESPACE) 

    find_package(SWIG 3.0 REQUIRED)
    include(${SWIG_USE_FILE})

    
    #Workaround SWIG targets not being exposed to cmake.
    get_property(TARGETDRIVER_INCLUDES TARGET TargetDriver PROPERTY INTERFACE_INCLUDE_DIRECTORIES)
    include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include ${TARGETDRIVER_INCLUDES} ${NUMPY_INCLUDE_DIR} ${PYTHON_INCLUDE_DIRS} ${CFITSIO_INCLUDE_DIRS})
    get_property(TargetIO_COMPILE_OPTIONS TARGET TargetIO PROPERTY INTERFACE_COMPILE_OPTIONS)
    string (REPLACE ";" " " TargetIO_COMPILE_OPTIONS_STR "${TargetIO_COMPILE_OPTIONS}")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D__STDC_FORMAT_MACROS  ${TargetIO_COMPILE_OPTIONS_STR}" )
    set_source_files_properties(target_io.i PROPERTIES CPLUSPLUS ON)
    swig_add_module(target_io python target_io.i ${SOURCES})
    
    #On OSX we need to tell the linker to not bother with undefined symbols
    if(APPLE)
      SET_TARGET_PROPERTIES(_target_io PROPERTIES LINK_FLAGS "-undefined dynamic_lookup")
    endif(APPLE)
    
    swig_link_libraries(target_io ${PYTHON_LIBRARIES} ${EXTLIBS} TargetDriver)

    set(PYTHON_SITE_PACKAGES "")
    execute_process(COMMAND python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())" OUTPUT_VARIABLE PYTHON_SITE_PACKAGES OUTPUT_STRIP_TRAILING_WHITESPACE)
    install(TARGETS _target_io DESTINATION ${PYTHON_SITE_PACKAGES})
    install(FILES ${PROJECT_BINARY_DIR}/target_io.py DESTINATION ${PYTHON_SITE_PACKAGES} COMPONENT pylibrary)
    message(STATUS "Python support is added")
  endif(PYTHON_EXECUTABLE)
endif(PYTHON)
