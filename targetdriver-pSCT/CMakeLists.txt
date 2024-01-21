cmake_minimum_required(VERSION 3.20 FATAL_ERROR)

# Project name
project(TargetDriver)
set(TargetDriver_VERSION_MAJOR 1)
set(TargetDriver_VERSION_MINOR 0)

if(POLICY CMP0078)
  cmake_policy(SET CMP0078 NEW)
endif()
if(POLICY CMP0086)
  cmake_policy(SET CMP0086 NEW)
endif()
if(POLICY CMP0054)
  cmake_policy(SET CMP0054 NEW)
endif()

option(PYTHON "Build the Python wrapper" ON)
option(UNITTEST "Enable unit test" OFF)
option(COMPILER_WARNINGS "Turn compiler warnings on" OFF)

#Check that that we have rt lib.
include(CheckLibraryExists)
check_library_exists(rt clock_gettime "time.h" HAVE_CLOCK_GETTIME)
if (HAVE_CLOCK_GETTIME)
  list(APPEND EXTLIBS rt)   
endif()

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


#Core library
aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/src SOURCES)
add_library(TargetDriver SHARED ${SOURCES})

#Set compiler options
if("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang" OR "${CMAKE_CXX_COMPILER_ID}" STREQUAL "AppleClang")
  target_compile_options(TargetDriver PUBLIC -std=c++23 -stdlib=libc++)
elseif("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU")
  execute_process(COMMAND ${CMAKE_C_COMPILER} -dumpversion OUTPUT_VARIABLE GCC_VERSION)
  if(GCC_VERSION VERSION_GREATER 4.7 OR GCC_VERSION VERSION_EQUAL 4.7)
    target_compile_options(TargetDriver PUBLIC -std=c++23)
  else()
    target_compile_options(TargetDriver PUBLIC -std=c++23)
  endif()
endif()
target_compile_options(TargetDriver PUBLIC -O2 -Wall)

#Set compiler warnings
if(COMPILER_WARNINGS)
    target_compile_options(TargetDrive PUBLIC -Wextra -Wconversion)
endif()

target_include_directories (TargetDriver
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

target_link_libraries(TargetDriver PUBLIC ${EXTLIBS})

target_compile_definitions (TargetDriver
  PUBLIC
    TARGETDRIVER_VERSION="${TargetDriver_VERSION_MAJOR}.${TargetDriver_VERSION_MINOR}"
    TARGET_BUILD_PATH="${CMAKE_BINARY_DIR}"
    TARGET_INSTALL_PATH="${CMAKE_INSTALL_PREFIX}"
)

set_target_properties (TargetDriver
  PROPERTIES 
    SOVERSION "${TargetDriver_VERSION_MAJOR}.${TargetDriver_VERSION_MINOR}"
    VERSION "${TargetDriver_VERSION_MAJOR}.${TargetDriver_VERSION_MINOR}"
)

install (TARGETS TargetDriver EXPORT ${PROJECT_NAME}Config LIBRARY DESTINATION lib)
install (DIRECTORY ${PROJECT_SOURCE_DIR}/include/ DESTINATION include)

# -----------------------------------------------------------------------------
# Export targets for use in downstream CMake projects
# -----------------------------------------------------------------------------

include ( CMakePackageConfigHelpers )
# Make importable from build directory
write_basic_package_version_file(
  "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}ConfigVersion.cmake"
  VERSION ${TargetDriver_VERSION_MAJOR}
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
file(GLOB CONFIG_FILES "${CMAKE_CURRENT_SOURCE_DIR}/config/*")
file(COPY ${CONFIG_FILES} DESTINATION ${CMAKE_BINARY_DIR}/share/${PROJECT_NAME}/config/) 

# Copy cfg files into install directory
install(DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/config" DESTINATION share/${PROJECT_NAME}/)

#------------------------------------------------------------------------------
# Tools
#------------------------------------------------------------------------------

set(
    CMAKE_RUNTIME_OUTPUT_DIRECTORY
    ${CMAKE_BINARY_DIR}/bin
    )

SET(EXE_NAMES tester testerT7 testerT7BP testerTC generate_markdown_files testbuffer update_firmware)

list(APPEND EXTLIBS pthread)
foreach(EXE_NAME ${EXE_NAMES})
  add_executable(${EXE_NAME} ${CMAKE_CURRENT_SOURCE_DIR}/src_exe/${EXE_NAME}.cc)
  target_link_libraries(${EXE_NAME} TargetDriver ${EXTLIBS})
endforeach()

install (TARGETS ${EXE_NAMES} RUNTIME DESTINATION bin)

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
    target_include_directories(${TEST_NAME} PRIVATE  TargetDriver ${Boost_INCLUDE_DIRS})
    add_test(NAME ${TEST_NAME} COMMAND ${TEST_NAME})
    list(APPEND TEST_EXE_NAMES ${TEST_NAME})
    target_link_libraries(${TEST_NAME} TargetDriver ${EXTLIBS})
  endforeach()
  message(STATUS "Unit tests is added")
endif(UNITTEST)

#------------------------------------------------------------------------------
# Python bindings
#------------------------------------------------------------------------------
if(PYTHON)
  #TODO: This whole section is fragile due to the way the SWIG module works.
  #This should be placed in it's own directory with it's own CMakeLists.txt.
  
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
    
    
    #Workaround SWIG targets not being exposed to cmake.
    include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include ${NUMPY_INCLUDE_DIR} ${PYTHON_INCLUDE_DIRS})
    get_property(TargetDriver_COMPILE_OPTIONS TARGET TargetDriver PROPERTY INTERFACE_COMPILE_OPTIONS)
    string (REPLACE ";" " " TargetDriver_COMPILE_OPTIONS_STR "${TargetDriver_COMPILE_OPTIONS}")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D__STDC_FORMAT_MACROS  ${TargetDriver_COMPILE_OPTIONS_STR}" )
    set_source_files_properties(target_driver.i PROPERTIES CPLUSPLUS ON)
    #swig_add_module(target_driver python target_driver.i ${SOURCES})
    swig_add_library(target_driver LANGUAGE python SOURCES target_driver.i ${SOURCES})
    get_directory_property(OutputTargets DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} BUILDSYSTEM_TARGETS)
	message(STATUS "Targets in directory: ${OutputTargets}")
	#On OSX we need to tell the linker to not bother with undefined symbols
    if(APPLE)
      SET_TARGET_PROPERTIES(target_driver PROPERTIES LINK_FLAGS "-undefined dynamic_lookup")
    endif(APPLE)
    target_compile_definitions (target_driver
      PUBLIC
      TARGETDRIVER_VERSION="${TargetDriver_VERSION_MAJOR}.${TargetDriver_VERSION_MINOR}"
      TARGET_BUILD_PATH="${CMAKE_BINARY_DIR}"
      TARGET_INSTALL_PATH="${CMAKE_INSTALL_PREFIX}"
    )

    swig_link_libraries(target_driver ${PYTHON_LIBRARIES} ${EXTLIBS})
    
    set(PYTHON_SITE_PACKAGES "")
    execute_process(COMMAND python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())" OUTPUT_VARIABLE PYTHON_SITE_PACKAGES OUTPUT_STRIP_TRAILING_WHITESPACE)
    install(TARGETS target_driver DESTINATION ${PYTHON_SITE_PACKAGES})
    install(FILES ${PROJECT_BINARY_DIR}/target_driver.py DESTINATION ${PYTHON_SITE_PACKAGES} COMPONENT pylibrary)
    message(STATUS "Python support is added")
  endif(PYTHON_EXECUTABLE)

endif(PYTHON)

#------------------------------------------------------------------------------
# Docs
#------------------------------------------------------------------------------
find_package(Doxygen)
if(DOXYGEN_FOUND)
  configure_file(${CMAKE_CURRENT_SOURCE_DIR}/Doxyfile.in ${CMAKE_CURRENT_BINARY_DIR}/Doxyfile @ONLY)
  set(MD_INPUT_1 ${CMAKE_CURRENT_SOURCE_DIR}/config/older_firmware/TM5_FPGA_Firmware0xFEDA003C.def)
  set(MD_INPUT_2 ${CMAKE_CURRENT_SOURCE_DIR}/config/older_firmware/TM5_ASIC.def)
  set(MD_OUTPUT_1 TM5_FPGA_Firmware0xFEDA003C.md)
  set(MD_OUTPUT_2 T5_ASIC_Registers.md)
  add_custom_command(OUTPUT ${MD_OUTPUT_1} ${MD_OUTPUT_2}
    DEPENDS ${MD_INPUT_1} ${MD_INPUT_2} ${CMAKE_CURRENT_BINARY_DIR}/generate_markdown_files
    COMMAND ${CMAKE_CURRENT_BINARY_DIR}/generate_markdown_files
    ${MD_INPUT_1} ${MD_INPUT_2}
    ${MD_OUTPUT_1} ${MD_OUTPUT_2}
    )
  set(MD_INPUT_3 ${CMAKE_CURRENT_SOURCE_DIR}/config/older_firmware/TM5_FPGA_Firmware0xFEDA003D.def)
  set(MD_OUTPUT_3 TM5_FPGA_Firmware0xFEDA003D.md)
  add_custom_command(OUTPUT ${MD_OUTPUT_3} ${MD_OUTPUT_2}
    DEPENDS ${MD_INPUT_3} ${MD_INPUT_2} ${CMAKE_CURRENT_BINARY_DIR}/generate_markdown_files
    COMMAND ${CMAKE_CURRENT_BINARY_DIR}/generate_markdown_files
    ${MD_INPUT_3} ${MD_INPUT_2}
    ${MD_OUTPUT_3} ${MD_OUTPUT_2}
    )
#target 7 documentation
  set(MD_INPUT_4 ${CMAKE_CURRENT_SOURCE_DIR}/config/older_firmware/TM7_FPGA_Firmware0xFEDA0003.def)
  set(MD_INPUT_5 ${CMAKE_CURRENT_SOURCE_DIR}/config/older_firmware/TM7_ASIC.def)
    set(MD_OUTPUT_4 TM7_FPGA_Firmware0xFEDA0003.md)
  set(MD_OUTPUT_5 T7_ASIC_Registers.md)
  add_custom_command(OUTPUT ${MD_OUTPUT_4} ${MD_OUTPUT_5}
    DEPENDS ${MD_INPUT_4} ${MD_INPUT_5} ${CMAKE_CURRENT_BINARY_DIR}/generate_markdown_files
    COMMAND ${CMAKE_CURRENT_BINARY_DIR}/generate_markdown_files
    ${MD_INPUT_4} ${MD_INPUT_5}
    ${MD_OUTPUT_4} ${MD_OUTPUT_5}
    )
  set(MD_INPUT_6 ${CMAKE_CURRENT_SOURCE_DIR}/config/older_firmware/TM7_FPGA_Firmware0xB0000102.def)
  set(MD_OUTPUT_6 TM7_FPGA_Firmware0xB0000102.md)
  add_custom_command(OUTPUT ${MD_OUTPUT_6} ${MD_OUTPUT_5}
    DEPENDS ${MD_INPUT_6} ${MD_INPUT_5} ${CMAKE_CURRENT_BINARY_DIR}/generate_markdown_files
    COMMAND ${CMAKE_CURRENT_BINARY_DIR}/generate_markdown_files
    ${MD_INPUT_6} ${MD_INPUT_5}
    ${MD_OUTPUT_6} ${MD_OUTPUT_5}
    )
#target EC documentation, intial version with one ASIC
  set(MD_INPUT_7 ${CMAKE_CURRENT_SOURCE_DIR}/config/older_firmware/TEC_FPGA_Firmware0xFEDA0001.def)
  set(MD_INPUT_8 ${CMAKE_CURRENT_SOURCE_DIR}/config/older_firmware/TEC_ASIC.def)
  set(MD_OUTPUT_7 TEC_FPGA_Firmware0xFEDA0001.md)
  set(MD_OUTPUT_8 TEC_ASIC_Registers.md)
  add_custom_command(OUTPUT ${MD_OUTPUT_7} ${MD_OUTPUT_8}
    DEPENDS ${MD_INPUT_7} ${MD_INPUT_8} ${CMAKE_CURRENT_BINARY_DIR}/generate_markdown_files
    COMMAND ${CMAKE_CURRENT_BINARY_DIR}/generate_markdown_files
    ${MD_INPUT_7} ${MD_INPUT_8}
    ${MD_OUTPUT_7} ${MD_OUTPUT_8}
    )
#TARGET C/T5TEA eval board documentation, just trigger ASIC
  set(MD_INPUT_9 ${CMAKE_CURRENT_SOURCE_DIR}/config/older_firmware/TECT5TEA_FPGA_Firmware0xFEDA0008.def)
  set(MD_INPUT_10 ${CMAKE_CURRENT_SOURCE_DIR}/config/T5TEA_ASIC.def)
  set(MD_OUTPUT_9 TECT5TEA_FPGA_Firmware0xFEDA0008.md)
  set(MD_OUTPUT_10 T5TEA_ASIC.md)
  add_custom_command(OUTPUT ${MD_OUTPUT_9} ${MD_OUTPUT_10}
    DEPENDS ${MD_INPUT_9} ${MD_INPUT_10} ${CMAKE_CURRENT_BINARY_DIR}/generate_markdown_files
    COMMAND ${CMAKE_CURRENT_BINARY_DIR}/generate_markdown_files
    ${MD_INPUT_9} ${MD_INPUT_10}
    ${MD_OUTPUT_9} ${MD_OUTPUT_10}
  )
  add_custom_target(doc
    ${DOXYGEN_EXECUTABLE} ${CMAKE_CURRENT_BINARY_DIR}/Doxyfile
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
    COMMENT "Generating API documentation with Doxygen" VERBATIM
    DEPENDS ${MD_OUTPUT_1} ${MD_OUTPUT_2} ${MD_OUTPUT_3}
    ${MD_OUTPUT_4} ${MD_OUTPUT_5} ${MD_OUTPUT_6} ${MD_OUTPUT_7}
    ${MD_OUTPUT_8} ${MD_OUTPUT_9} ${MD_OUTPUT_10}
    )
endif(DOXYGEN_FOUND)
