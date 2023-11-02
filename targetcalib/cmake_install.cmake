# Install script for directory: /Users/white/Software/chec/TargetDriver/source

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/usr/local")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

if(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "library")
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE SHARED_LIBRARY FILES "/Users/white/Software/chec/TargetDriver/source/libTargetDriver.dylib")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libTargetDriver.dylib" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libTargetDriver.dylib")
    execute_process(COMMAND "/usr/bin/install_name_tool"
      -id "libTargetDriver.dylib"
      "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libTargetDriver.dylib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libTargetDriver.dylib")
    endif()
  endif()
endif()

if(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "headers")
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/TargetDriver" TYPE FILE FILES
    "/Users/white/Software/chec/TargetDriver/source/include/TargetDriver/DataListener.h"
    "/Users/white/Software/chec/TargetDriver/source/include/TargetDriver/EventBuffer.h"
    "/Users/white/Software/chec/TargetDriver/source/include/TargetDriver/EventHeader.h"
    "/Users/white/Software/chec/TargetDriver/source/include/TargetDriver/RawEvent.h"
    "/Users/white/Software/chec/TargetDriver/source/include/TargetDriver/TargetModule.h"
    "/Users/white/Software/chec/TargetDriver/source/include/TargetDriver/TargetSettings.h"
    "/Users/white/Software/chec/TargetDriver/source/include/TargetDriver/TargetSimulator.h"
    "/Users/white/Software/chec/TargetDriver/source/include/TargetDriver/TClient.h"
    "/Users/white/Software/chec/TargetDriver/source/include/TargetDriver/TComms.h"
    "/Users/white/Software/chec/TargetDriver/source/include/TargetDriver/TDataPacket.h"
    "/Users/white/Software/chec/TargetDriver/source/include/TargetDriver/TesterBoard.h"
    "/Users/white/Software/chec/TargetDriver/source/include/TargetDriver/TServer.h"
    "/Users/white/Software/chec/TargetDriver/source/include/TargetDriver/TWaveform.h"
    )
endif()

if(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "Unspecified")
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/usr/local/Cellar/python/2.7.10_2/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/_target_driver.so")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
file(INSTALL DESTINATION "/usr/local/Cellar/python/2.7.10_2/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages" TYPE MODULE FILES "/Users/white/Software/chec/TargetDriver/source/_target_driver.so")
  if(EXISTS "$ENV{DESTDIR}/usr/local/Cellar/python/2.7.10_2/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/_target_driver.so" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}/usr/local/Cellar/python/2.7.10_2/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/_target_driver.so")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/strip" "$ENV{DESTDIR}/usr/local/Cellar/python/2.7.10_2/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/_target_driver.so")
    endif()
  endif()
endif()

if(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "pylibrary")
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/usr/local/Cellar/python/2.7.10_2/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/target_driver.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
file(INSTALL DESTINATION "/usr/local/Cellar/python/2.7.10_2/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages" TYPE FILE FILES "/Users/white/Software/chec/TargetDriver/source/target_driver.py")
endif()

if(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "devel")
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/TargetDriver" TYPE FILE FILES "/Users/white/Software/chec/TargetDriver/source/TargetDriverConfig.cmake")
endif()

if(CMAKE_INSTALL_COMPONENT)
  set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INSTALL_COMPONENT}.txt")
else()
  set(CMAKE_INSTALL_MANIFEST "install_manifest.txt")
endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
file(WRITE "/Users/white/Software/chec/TargetDriver/source/${CMAKE_INSTALL_MANIFEST}"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
