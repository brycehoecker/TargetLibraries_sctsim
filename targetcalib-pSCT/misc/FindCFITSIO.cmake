# Find fitsio.h and cfitsio library
# Ref. http://www.cmake.org/Wiki/CMake:How_To_Find_Librarie

find_path(CFITSIO_INCLUDE_DIR fitsio.h)

# For the default yum configuration on CentOS 7
if(CFITSIO_INCLUDE_DIR STREQUAL "CFITSIO_INCLUDE_DIR-NOTFOUND")
  find_path(CFITSIO_INCLUDE_DIR cfitsio/fitsio.h)
  if(NOT CFITSIO_INCLUDE_DIR STREQUAL "CFITSIO_INCLUDE_DIR-NOTFOUND")
    set(CFITSIO_INCLUDE_DIR "${CFITSIO_INCLUDE_DIR}/cfitsio")
  endif()
endif()

find_library(CFITSIO_LIBRARY cfitsio)
set(CFITSIO_INCLUDE_DIRS ${CFITSIO_INCLUDE_DIR})
set(CFITSIO_LIBRARIES ${CFITSIO_LIBRARY})
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(CFITSIO DEFAULT_MSG CFITSIO_LIBRARY CFITSIO_INCLUDE_DIR)
mark_as_advanced(CFITSIO_INCLUDE_DIR CFITSIO_LIBRARY)