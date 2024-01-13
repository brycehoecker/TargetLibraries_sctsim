#!/bin/bash

#Bryces script for creating the conda enviornment
echo "Script for creating a psct conda enviornment with python=3.7"

source ~/.bashrc
conda init

# Ask the user for the environment name
echo "Enter the name of the conda environment:"
read env_name

# Create a new environment with the given name and Python 3.7
conda create -n "$env_name" python=3.7 -y

# Activate the environment
conda activate "$env_name"

# Add the "conda-forge" channel
conda config --add channels conda-forge

# Install specific versions of packages
conda install cmake=3.16 -y
conda install swig=4.0.2 -y

# Install multiple packages at once
conda install matplotlib numpy cfitsio -y
