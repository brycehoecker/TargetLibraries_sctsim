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
CMAKE_SOURCE_DIR = /home/sctsim/git_repos/TargetLibraries/targetcalib

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /home/sctsim/git_repos/TargetLibraries/targetcalib/build

# Include any dependencies generated for this target.
include CMakeFiles/fix_bad_tfs.dir/depend.make
# Include any dependencies generated by the compiler for this target.
include CMakeFiles/fix_bad_tfs.dir/compiler_depend.make

# Include the progress variables for this target.
include CMakeFiles/fix_bad_tfs.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/fix_bad_tfs.dir/flags.make

CMakeFiles/fix_bad_tfs.dir/src_exe/fix_bad_tfs.cc.o: CMakeFiles/fix_bad_tfs.dir/flags.make
CMakeFiles/fix_bad_tfs.dir/src_exe/fix_bad_tfs.cc.o: ../src_exe/fix_bad_tfs.cc
CMakeFiles/fix_bad_tfs.dir/src_exe/fix_bad_tfs.cc.o: CMakeFiles/fix_bad_tfs.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/sctsim/git_repos/TargetLibraries/targetcalib/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building CXX object CMakeFiles/fix_bad_tfs.dir/src_exe/fix_bad_tfs.cc.o"
	/usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -MD -MT CMakeFiles/fix_bad_tfs.dir/src_exe/fix_bad_tfs.cc.o -MF CMakeFiles/fix_bad_tfs.dir/src_exe/fix_bad_tfs.cc.o.d -o CMakeFiles/fix_bad_tfs.dir/src_exe/fix_bad_tfs.cc.o -c /home/sctsim/git_repos/TargetLibraries/targetcalib/src_exe/fix_bad_tfs.cc

CMakeFiles/fix_bad_tfs.dir/src_exe/fix_bad_tfs.cc.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing CXX source to CMakeFiles/fix_bad_tfs.dir/src_exe/fix_bad_tfs.cc.i"
	/usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -E /home/sctsim/git_repos/TargetLibraries/targetcalib/src_exe/fix_bad_tfs.cc > CMakeFiles/fix_bad_tfs.dir/src_exe/fix_bad_tfs.cc.i

CMakeFiles/fix_bad_tfs.dir/src_exe/fix_bad_tfs.cc.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling CXX source to assembly CMakeFiles/fix_bad_tfs.dir/src_exe/fix_bad_tfs.cc.s"
	/usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -S /home/sctsim/git_repos/TargetLibraries/targetcalib/src_exe/fix_bad_tfs.cc -o CMakeFiles/fix_bad_tfs.dir/src_exe/fix_bad_tfs.cc.s

# Object files for target fix_bad_tfs
fix_bad_tfs_OBJECTS = \
"CMakeFiles/fix_bad_tfs.dir/src_exe/fix_bad_tfs.cc.o"

# External object files for target fix_bad_tfs
fix_bad_tfs_EXTERNAL_OBJECTS =

bin/fix_bad_tfs: CMakeFiles/fix_bad_tfs.dir/src_exe/fix_bad_tfs.cc.o
bin/fix_bad_tfs: CMakeFiles/fix_bad_tfs.dir/build.make
bin/fix_bad_tfs: libTargetCalib.so.1.0
bin/fix_bad_tfs: /usr/lib64/libcfitsio.so
bin/fix_bad_tfs: /usr/lib/libTargetIO.so.1.0
bin/fix_bad_tfs: /usr/lib64/libcfitsio.so
bin/fix_bad_tfs: /usr/lib/libTargetDriver.so.1.0
bin/fix_bad_tfs: CMakeFiles/fix_bad_tfs.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --bold --progress-dir=/home/sctsim/git_repos/TargetLibraries/targetcalib/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_2) "Linking CXX executable bin/fix_bad_tfs"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/fix_bad_tfs.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/fix_bad_tfs.dir/build: bin/fix_bad_tfs
.PHONY : CMakeFiles/fix_bad_tfs.dir/build

CMakeFiles/fix_bad_tfs.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/fix_bad_tfs.dir/cmake_clean.cmake
.PHONY : CMakeFiles/fix_bad_tfs.dir/clean

CMakeFiles/fix_bad_tfs.dir/depend:
	cd /home/sctsim/git_repos/TargetLibraries/targetcalib/build && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /home/sctsim/git_repos/TargetLibraries/targetcalib /home/sctsim/git_repos/TargetLibraries/targetcalib /home/sctsim/git_repos/TargetLibraries/targetcalib/build /home/sctsim/git_repos/TargetLibraries/targetcalib/build /home/sctsim/git_repos/TargetLibraries/targetcalib/build/CMakeFiles/fix_bad_tfs.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/fix_bad_tfs.dir/depend

