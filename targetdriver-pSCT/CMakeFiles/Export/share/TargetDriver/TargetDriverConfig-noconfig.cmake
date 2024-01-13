#----------------------------------------------------------------
# Generated CMake target import file.
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "TargetDriver" for configuration ""
set_property(TARGET TargetDriver APPEND PROPERTY IMPORTED_CONFIGURATIONS NOCONFIG)
set_target_properties(TargetDriver PROPERTIES
  IMPORTED_LOCATION_NOCONFIG "${_IMPORT_PREFIX}/lib/libTargetDriver.so.1.0"
  IMPORTED_SONAME_NOCONFIG "libTargetDriver.so.1.0"
  )

list(APPEND _IMPORT_CHECK_TARGETS TargetDriver )
list(APPEND _IMPORT_CHECK_FILES_FOR_TargetDriver "${_IMPORT_PREFIX}/lib/libTargetDriver.so.1.0" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
