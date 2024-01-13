#!/bin/bash

# Change to the PSCTTargetDriver directory
cd targetdriver/

rm -rf build/
mkdir build
cd build

cmake ../ -DCMAKE_INSTALL_PREFIX=$CONDA_PREFIX
