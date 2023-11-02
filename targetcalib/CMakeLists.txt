cmake_minimum_required(VERSION 3.0 FATAL_ERROR)

# Project name
project(TargetCalib)
set(TargetCalib_VERSION_MAJOR 1)
set(TargetCalib_VERSION_MINOR 0)

option(PYTHON "Build the Python wrapper" ON)
option(UNITTEST "Enable unit test" OFF)
option(COMPILER_WARNINGS "Turn compiler warnings on" OFF)


# TargetDriver
if(TARGET TargetDriver)
    message(STATUS "Building against bundle TargetDriver")
else()
    find_package(TargetDriver REQUIRED NO_MODULE)
endif()


# TargetIO
if(TARGET TargetIO)
    message(STATUS "Building against bundled TargetIO")
else()
    find_package(TargetIO REQUIRED NO_MODULE )
endif()




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


aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/src SOURCES)
add_library(TargetCalib SHARED ${SOURCES})

#Set compiler options
if("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang" OR "${CMAKE_CXX_COMPILER_ID}" STREQUAL "AppleClang")
  target_compile_options(TargetCalib PUBLIC -std=c++11 -stdlib=libc++)
elseif("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU")
  execute_process(COMMAND ${CMAKE_C_COMPILER} -dumpversion OUTPUT_VARIABLE GCC_VERSION)
  if(GCC_VERSION VERSION_GREATER 4.7 OR GCC_VERSION VERSION_EQUAL 4.7)
    target_compile_options(TargetCalib PUBLIC -std=c++11)
  else()
    target_compile_options(TargetCalib PUBLIC -std=c++0x)
  endif()
endif()
target_compile_options(TargetCalib PUBLIC -O2)

#Set compiler warnings
if(COMPILER_WARNINGS)
    target_compile_options(TargetCalib PUBLIC -Wall -Wextra -Wconversion)
endif()

target_include_directories (TargetCalib
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
    ${CFITSIO_INCLUDE_DIRS}
)

target_link_libraries(TargetCalib ${EXTLIBS} TargetDriver TargetIO)

target_compile_definitions (TargetCalib
  PUBLIC
    TARGET_IO_VERSION="${TargetCalib_VERSION_MAJOR}.${TargetCalib_VERSION_MINOR}"
)

set_target_properties (TargetCalib
  PROPERTIES 
    SOVERSION "${TargetCalib_VERSION_MAJOR}.${TargetCalib_VERSION_MINOR}"
    VERSION "${TargetCalib_VERSION_MAJOR}.${TargetCalib_VERSION_MINOR}"
)


install (TARGETS TargetCalib EXPORT ${PROJECT_NAME}Config LIBRARY DESTINATION lib)
install (DIRECTORY ${PROJECT_SOURCE_DIR}/include/ DESTINATION include)


# -----------------------------------------------------------------------------
# Export targets for use in downstream CMake projects
# -----------------------------------------------------------------------------

include ( CMakePackageConfigHelpers )
# Make importable from build directory
write_basic_package_version_file(
  "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}ConfigVersion.cmake"
  VERSION ${TargetCalib_VERSION_MAJOR}.${TargetCalib_VERSION_MINOR}
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

#-----
# Copy cfg files into build
file(GLOB CONFIG_FILES "${CMAKE_CURRENT_SOURCE_DIR}/dev/*")
file(COPY ${CONFIG_FILES} DESTINATION ${CMAKE_BINARY_DIR}/share/${PROJECT_NAME}/dev/) 

# Copy cfg files into install directory
install(DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/dev" DESTINATION share/${PROJECT_NAME})

#------------------------------------------------------------------------------
# Tools
#------------------------------------------------------------------------------
set(
    CMAKE_RUNTIME_OUTPUT_DIRECTORY
    ${CMAKE_BINARY_DIR}/bin
    )

SET(EXE_NAMES generate_ped generate_dc_tf apply_calibration fix_tf_offset fix_bad_tfs create_pedestal_tfinput)
foreach(EXE_NAME ${EXE_NAMES})
  add_executable(${EXE_NAME} ${CMAKE_CURRENT_SOURCE_DIR}/src_exe/${EXE_NAME}.cc)
  target_include_directories(${EXE_NAME} PRIVATE ${CFITSIO_INCLUDE_DIRS})
  target_link_libraries(${EXE_NAME} TargetCalib ${EXTLIBS})
  endforeach()
install (TARGETS ${EXE_NAMES} RUNTIME DESTINATION bin)

if(AC)
  find_package(ROOT REQUIRED)
  include(${ROOT_USE_FILE})
  list(APPEND EXTLIBS ${ROOT_LIBRARIES})

  SET(EXE_NAMES generate_ac_tf)# generate_ac_tf_jason)
  foreach(EXE_NAME ${EXE_NAMES})
    add_executable(${EXE_NAME} ${CMAKE_CURRENT_SOURCE_DIR}/src_exe/${EXE_NAME}.cc)
    target_link_libraries(${EXE_NAME} TargetCalib ${EXTLIBS})
    install(TARGETS ${EXE_NAME} RUNTIME DESTINATION .)
  endforeach()
endif(AC)

install(PROGRAMS ${CMAKE_CURRENT_SOURCE_DIR}/scripts/apply_calibration_multicore DESTINATION bin)

#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------
if(UNITTEST)
  message("Unit test is added")
  # Find the Boost unit test framework
  find_package(Boost COMPONENTS unit_test_framework REQUIRED)
  ADD_DEFINITIONS(-DBOOST_ALL_DYN_LINK)
  # include_directories(${Boost_INCLUDE_DIRS}) 
  list(APPEND EXTLIBS ${Boost_LIBRARIES})

  enable_testing()
  aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/test TEST_NAMES)
  foreach(TEST_NAME ${TEST_NAMES})
    get_filename_component(TEST_NAME ${TEST_NAME} NAME_WE)
    add_executable(${TEST_NAME} ${CMAKE_CURRENT_SOURCE_DIR}/test/${TEST_NAME}.cc)
    add_test(NAME ${TEST_NAME} COMMAND ${TEST_NAME})
    target_include_directories(${TEST_NAME} PRIVATE ${Boost_INCLUDE_DIRS})
    list(APPEND TEST_EXE_NAMES ${TEST_NAME})
    target_link_libraries(${TEST_NAME} TargetCalib TargetDriver TargetIO ${EXTLIBS})
  endforeach()
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

    #execute_process(COMMAND python -c "import numpy; print(numpy.get_include())" OUTPUT_VARIABLE NUMPY_INCLUDE_DIR OUTPUT_STRIP_TRAILING_WHITESPACE)
    #Workaround SWIG targets not being exposed to cmake.
    get_property(TARGETDRIVER_INCLUDES TARGET TargetDriver PROPERTY INTERFACE_INCLUDE_DIRECTORIES)
    get_property(TARGETIO_INCLUDES TARGET TargetIO PROPERTY INTERFACE_INCLUDE_DIRECTORIES)
    include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include ${TARGETIO_INCLUDES} ${TARGETDRIVER_INCLUDES} ${NUMPY_INCLUDE_DIR} ${PYTHON_INCLUDE_DIRS} ${CFITSIO_INCLUDE_DIRS})
    get_property(TargetCalib_COMPILE_OPTIONS TARGET TargetCalib PROPERTY INTERFACE_COMPILE_OPTIONS)
    string (REPLACE ";" " " TargetCalib_COMPILE_OPTIONS_STR "${TargetCalib_COMPILE_OPTIONS}")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D__STDC_FORMAT_MACROS  ${TargetCalib_COMPILE_OPTIONS_STR}" )

    set_source_files_properties(target_calib.i PROPERTIES CPLUSPLUS ON)
    swig_add_module(_target_calib python target_calib.i ${SOURCES})
    #On OSX we need to tell the linker to not bother with undefined symbols
    if(APPLE)
      SET_TARGET_PROPERTIES(_target_calib PROPERTIES LINK_FLAGS "-undefined dynamic_lookup")
    endif(APPLE)
    swig_link_libraries(_target_calib ${PYTHON_LIBRARIES} ${EXTLIBS})
    
    set(PYTHON_SITE_PACKAGES "")
    execute_process(COMMAND python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())" OUTPUT_VARIABLE PYTHON_SITE_PACKAGES OUTPUT_STRIP_TRAILING_WHITESPACE)
    install(TARGETS _target_calib DESTINATION ${PYTHON_SITE_PACKAGES})
    install(FILES ${PROJECT_BINARY_DIR}/target_calib.py DESTINATION ${PYTHON_SITE_PACKAGES} COMPONENT pylibrary)
    message(STATUS "Python support is added")
  endif(PYTHON_EXECUTABLE)
endif(PYTHON)
