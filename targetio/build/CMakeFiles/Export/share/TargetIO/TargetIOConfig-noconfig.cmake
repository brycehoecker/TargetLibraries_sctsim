#----------------------------------------------------------------
# Generated CMake target import file.
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "TargetIO" for configuration ""
set_property(TARGET TargetIO APPEND PROPERTY IMPORTED_CONFIGURATIONS NOCONFIG)
set_target_properties(TargetIO PROPERTIES
  IMPORTED_LOCATION_NOCONFIG "${_IMPORT_PREFIX}/lib/libTargetIO.so.1.0"
  IMPORTED_SONAME_NOCONFIG "libTargetIO.so.1.0"
  )

list(APPEND _IMPORT_CHECK_TARGETS TargetIO )
list(APPEND _IMPORT_CHECK_FILES_FOR_TargetIO "${_IMPORT_PREFIX}/lib/libTargetIO.so.1.0" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
