#!/bin/bash

#Delete the old build directory and create a new one
rm -rf build/
mkdir build
cd build

# Run cmake in the build directory
cmake ..

# Run make in the build directory
make

# Run make install in the first directory
sudo make install

# Repeat the above steps for additional directories if needed
