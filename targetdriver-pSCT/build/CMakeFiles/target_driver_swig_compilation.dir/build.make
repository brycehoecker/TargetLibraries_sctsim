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
CMAKE_SOURCE_DIR = /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/build

# Utility rule file for target_driver_swig_compilation.

# Include any custom commands dependencies for this target.
include CMakeFiles/target_driver_swig_compilation.dir/compiler_depend.make

# Include the progress variables for this target.
include CMakeFiles/target_driver_swig_compilation.dir/progress.make

CMakeFiles/target_driver_swig_compilation: CMakeFiles/target_driver.dir/target_driverPYTHON.stamp

CMakeFiles/target_driver.dir/target_driverPYTHON.stamp: ../target_driver.i
CMakeFiles/target_driver.dir/target_driverPYTHON.stamp: ../target_driver.i
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --blue --bold --progress-dir=/home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Swig compile target_driver.i for python"
	/usr/bin/cmake -E make_directory /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/build /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/build/CMakeFiles/target_driver.dir
	/usr/bin/cmake -E touch /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/build/CMakeFiles/target_driver.dir/target_driverPYTHON.stamp
	/usr/bin/cmake -E env SWIG_LIB=/usr/share/swig/4.0.2 /usr/bin/swig -python -outdir /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/build -c++ -interface _target_driver -I/home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/include -I/home/sctsim/.local/lib/python3.9/site-packages/numpy/core/include -I/usr/include/python3.9 -o /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/build/CMakeFiles/target_driver.dir/target_driverPYTHON_wrap.cxx /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/target_driver.i

target_driver_swig_compilation: CMakeFiles/target_driver.dir/target_driverPYTHON.stamp
target_driver_swig_compilation: CMakeFiles/target_driver_swig_compilation
target_driver_swig_compilation: CMakeFiles/target_driver_swig_compilation.dir/build.make
.PHONY : target_driver_swig_compilation

# Rule to build all files generated by this target.
CMakeFiles/target_driver_swig_compilation.dir/build: target_driver_swig_compilation
.PHONY : CMakeFiles/target_driver_swig_compilation.dir/build

CMakeFiles/target_driver_swig_compilation.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/target_driver_swig_compilation.dir/cmake_clean.cmake
.PHONY : CMakeFiles/target_driver_swig_compilation.dir/clean

CMakeFiles/target_driver_swig_compilation.dir/depend:
	cd /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/build && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/build /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/build /home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/build/CMakeFiles/target_driver_swig_compilation.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/target_driver_swig_compilation.dir/depend

