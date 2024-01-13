# CMAKE generated file: DO NOT EDIT!
# Generated by "Unix Makefiles" Generator, CMake Version 3.20

# Delete rule output on recipe failure.
.DELETE_ON_ERROR:

#=============================================================================
# Special targets provided by cmake.

# Disable implicit rules so canonical targets will work.
.SUFFIXES:

# Disable VCS-based implicit rules.
% : %,v

# Disable VCS-based implicit rules.
% : RCS/%

# Disable VCS-based implicit rules.
% : RCS/%,v

# Disable VCS-based implicit rules.
% : SCCS/s.%

# Disable VCS-based implicit rules.
% : s.%

.SUFFIXES: .hpux_make_needs_suffix_list

# Produce verbose output by default.
VERBOSE = 1

# Command-line flag to silence nested $(MAKE).
$(VERBOSE)MAKESILENT = -s

#Suppress display of executed commands.
$(VERBOSE).SILENT:

# A target that is always out of date.
cmake_force:
.PHONY : cmake_force

#=============================================================================
# Set environment variables for the build.

# The shell in which to execute make rules.
SHELL = /bin/sh

# The CMake executable.
CMAKE_COMMAND = /usr/bin/cmake

# The command to remove a file.
RM = /usr/bin/cmake -E rm -f

# Escaping for special characters.
EQUALS = =

# The top-level source directory on which CMake was run.
CMAKE_SOURCE_DIR = /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT

# Include any dependencies generated for this target.
include CMakeFiles/tester.dir/depend.make
# Include any dependencies generated by the compiler for this target.
include CMakeFiles/tester.dir/compiler_depend.make

# Include the progress variables for this target.
include CMakeFiles/tester.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/tester.dir/flags.make

CMakeFiles/tester.dir/src_exe/tester.cc.o: CMakeFiles/tester.dir/flags.make
CMakeFiles/tester.dir/src_exe/tester.cc.o: src_exe/tester.cc
CMakeFiles/tester.dir/src_exe/tester.cc.o: CMakeFiles/tester.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building CXX object CMakeFiles/tester.dir/src_exe/tester.cc.o"
	/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -MD -MT CMakeFiles/tester.dir/src_exe/tester.cc.o -MF CMakeFiles/tester.dir/src_exe/tester.cc.o.d -o CMakeFiles/tester.dir/src_exe/tester.cc.o -c /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/src_exe/tester.cc

CMakeFiles/tester.dir/src_exe/tester.cc.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing CXX source to CMakeFiles/tester.dir/src_exe/tester.cc.i"
	/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -E /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/src_exe/tester.cc > CMakeFiles/tester.dir/src_exe/tester.cc.i

CMakeFiles/tester.dir/src_exe/tester.cc.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling CXX source to assembly CMakeFiles/tester.dir/src_exe/tester.cc.s"
	/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -S /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/src_exe/tester.cc -o CMakeFiles/tester.dir/src_exe/tester.cc.s

# Object files for target tester
tester_OBJECTS = \
"CMakeFiles/tester.dir/src_exe/tester.cc.o"

# External object files for target tester
tester_EXTERNAL_OBJECTS =

bin/tester: CMakeFiles/tester.dir/src_exe/tester.cc.o
bin/tester: CMakeFiles/tester.dir/build.make
bin/tester: libTargetDriver.so.1.0
bin/tester: CMakeFiles/tester.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --bold --progress-dir=/home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/CMakeFiles --progress-num=$(CMAKE_PROGRESS_2) "Linking CXX executable bin/tester"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/tester.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/tester.dir/build: bin/tester
.PHONY : CMakeFiles/tester.dir/build

CMakeFiles/tester.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/tester.dir/cmake_clean.cmake
.PHONY : CMakeFiles/tester.dir/clean

CMakeFiles/tester.dir/depend:
	cd /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/CMakeFiles/tester.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/tester.dir/depend
