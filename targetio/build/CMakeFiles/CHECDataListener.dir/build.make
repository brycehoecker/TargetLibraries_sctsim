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
CMAKE_SOURCE_DIR = /home/sctsim/git_repos/TargetLibraries/targetio

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /home/sctsim/git_repos/TargetLibraries/targetio/build

# Include any dependencies generated for this target.
include CMakeFiles/CHECDataListener.dir/depend.make
# Include any dependencies generated by the compiler for this target.
include CMakeFiles/CHECDataListener.dir/compiler_depend.make

# Include the progress variables for this target.
include CMakeFiles/CHECDataListener.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/CHECDataListener.dir/flags.make

CMakeFiles/CHECDataListener.dir/examples/CHECDataListener.cc.o: CMakeFiles/CHECDataListener.dir/flags.make
CMakeFiles/CHECDataListener.dir/examples/CHECDataListener.cc.o: ../examples/CHECDataListener.cc
CMakeFiles/CHECDataListener.dir/examples/CHECDataListener.cc.o: CMakeFiles/CHECDataListener.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/sctsim/git_repos/TargetLibraries/targetio/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building CXX object CMakeFiles/CHECDataListener.dir/examples/CHECDataListener.cc.o"
	/usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -MD -MT CMakeFiles/CHECDataListener.dir/examples/CHECDataListener.cc.o -MF CMakeFiles/CHECDataListener.dir/examples/CHECDataListener.cc.o.d -o CMakeFiles/CHECDataListener.dir/examples/CHECDataListener.cc.o -c /home/sctsim/git_repos/TargetLibraries/targetio/examples/CHECDataListener.cc

CMakeFiles/CHECDataListener.dir/examples/CHECDataListener.cc.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing CXX source to CMakeFiles/CHECDataListener.dir/examples/CHECDataListener.cc.i"
	/usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -E /home/sctsim/git_repos/TargetLibraries/targetio/examples/CHECDataListener.cc > CMakeFiles/CHECDataListener.dir/examples/CHECDataListener.cc.i

CMakeFiles/CHECDataListener.dir/examples/CHECDataListener.cc.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling CXX source to assembly CMakeFiles/CHECDataListener.dir/examples/CHECDataListener.cc.s"
	/usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -S /home/sctsim/git_repos/TargetLibraries/targetio/examples/CHECDataListener.cc -o CMakeFiles/CHECDataListener.dir/examples/CHECDataListener.cc.s

# Object files for target CHECDataListener
CHECDataListener_OBJECTS = \
"CMakeFiles/CHECDataListener.dir/examples/CHECDataListener.cc.o"

# External object files for target CHECDataListener
CHECDataListener_EXTERNAL_OBJECTS =

bin/CHECDataListener: CMakeFiles/CHECDataListener.dir/examples/CHECDataListener.cc.o
bin/CHECDataListener: CMakeFiles/CHECDataListener.dir/build.make
bin/CHECDataListener: libTargetIO.so.1.0
bin/CHECDataListener: /usr/lib64/libcfitsio.so
bin/CHECDataListener: /usr/lib/libTargetDriver.so.1.0
bin/CHECDataListener: CMakeFiles/CHECDataListener.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --bold --progress-dir=/home/sctsim/git_repos/TargetLibraries/targetio/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_2) "Linking CXX executable bin/CHECDataListener"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/CHECDataListener.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/CHECDataListener.dir/build: bin/CHECDataListener
.PHONY : CMakeFiles/CHECDataListener.dir/build

CMakeFiles/CHECDataListener.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/CHECDataListener.dir/cmake_clean.cmake
.PHONY : CMakeFiles/CHECDataListener.dir/clean

CMakeFiles/CHECDataListener.dir/depend:
	cd /home/sctsim/git_repos/TargetLibraries/targetio/build && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /home/sctsim/git_repos/TargetLibraries/targetio /home/sctsim/git_repos/TargetLibraries/targetio /home/sctsim/git_repos/TargetLibraries/targetio/build /home/sctsim/git_repos/TargetLibraries/targetio/build /home/sctsim/git_repos/TargetLibraries/targetio/build/CMakeFiles/CHECDataListener.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/CHECDataListener.dir/depend

