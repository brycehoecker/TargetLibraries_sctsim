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
CMAKE_SOURCE_DIR = /home/sctsim/git_repos/TargetLibraries/targetdriver

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /home/sctsim/git_repos/TargetLibraries/targetdriver/build

# Include any dependencies generated for this target.
include CMakeFiles/generate_markdown_files.dir/depend.make
# Include any dependencies generated by the compiler for this target.
include CMakeFiles/generate_markdown_files.dir/compiler_depend.make

# Include the progress variables for this target.
include CMakeFiles/generate_markdown_files.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/generate_markdown_files.dir/flags.make

CMakeFiles/generate_markdown_files.dir/src_exe/generate_markdown_files.cc.o: CMakeFiles/generate_markdown_files.dir/flags.make
CMakeFiles/generate_markdown_files.dir/src_exe/generate_markdown_files.cc.o: ../src_exe/generate_markdown_files.cc
CMakeFiles/generate_markdown_files.dir/src_exe/generate_markdown_files.cc.o: CMakeFiles/generate_markdown_files.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/sctsim/git_repos/TargetLibraries/targetdriver/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building CXX object CMakeFiles/generate_markdown_files.dir/src_exe/generate_markdown_files.cc.o"
	/usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -MD -MT CMakeFiles/generate_markdown_files.dir/src_exe/generate_markdown_files.cc.o -MF CMakeFiles/generate_markdown_files.dir/src_exe/generate_markdown_files.cc.o.d -o CMakeFiles/generate_markdown_files.dir/src_exe/generate_markdown_files.cc.o -c /home/sctsim/git_repos/TargetLibraries/targetdriver/src_exe/generate_markdown_files.cc

CMakeFiles/generate_markdown_files.dir/src_exe/generate_markdown_files.cc.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing CXX source to CMakeFiles/generate_markdown_files.dir/src_exe/generate_markdown_files.cc.i"
	/usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -E /home/sctsim/git_repos/TargetLibraries/targetdriver/src_exe/generate_markdown_files.cc > CMakeFiles/generate_markdown_files.dir/src_exe/generate_markdown_files.cc.i

CMakeFiles/generate_markdown_files.dir/src_exe/generate_markdown_files.cc.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling CXX source to assembly CMakeFiles/generate_markdown_files.dir/src_exe/generate_markdown_files.cc.s"
	/usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -S /home/sctsim/git_repos/TargetLibraries/targetdriver/src_exe/generate_markdown_files.cc -o CMakeFiles/generate_markdown_files.dir/src_exe/generate_markdown_files.cc.s

# Object files for target generate_markdown_files
generate_markdown_files_OBJECTS = \
"CMakeFiles/generate_markdown_files.dir/src_exe/generate_markdown_files.cc.o"

# External object files for target generate_markdown_files
generate_markdown_files_EXTERNAL_OBJECTS =

bin/generate_markdown_files: CMakeFiles/generate_markdown_files.dir/src_exe/generate_markdown_files.cc.o
bin/generate_markdown_files: CMakeFiles/generate_markdown_files.dir/build.make
bin/generate_markdown_files: libTargetDriver.so.1.0
bin/generate_markdown_files: CMakeFiles/generate_markdown_files.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --bold --progress-dir=/home/sctsim/git_repos/TargetLibraries/targetdriver/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_2) "Linking CXX executable bin/generate_markdown_files"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/generate_markdown_files.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/generate_markdown_files.dir/build: bin/generate_markdown_files
.PHONY : CMakeFiles/generate_markdown_files.dir/build

CMakeFiles/generate_markdown_files.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/generate_markdown_files.dir/cmake_clean.cmake
.PHONY : CMakeFiles/generate_markdown_files.dir/clean

CMakeFiles/generate_markdown_files.dir/depend:
	cd /home/sctsim/git_repos/TargetLibraries/targetdriver/build && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /home/sctsim/git_repos/TargetLibraries/targetdriver /home/sctsim/git_repos/TargetLibraries/targetdriver /home/sctsim/git_repos/TargetLibraries/targetdriver/build /home/sctsim/git_repos/TargetLibraries/targetdriver/build /home/sctsim/git_repos/TargetLibraries/targetdriver/build/CMakeFiles/generate_markdown_files.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/generate_markdown_files.dir/depend

