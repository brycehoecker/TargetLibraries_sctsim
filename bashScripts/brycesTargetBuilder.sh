#!/bin/bash

# Define the target directory
echo -e "\e[32mStarting brycesTargetBuilder.sh Script\e[0m"
echo "The Current working directory is: $(pwd)"

dir="build"
# Check if the directory exists in the current location
if [ -d "$dir" ]; then
    echo "Directory $dir found in $(pwd). Deleting..."
    # Use the rm command to recursively force delete the directory and its contents
    sudo rm -rf "$dir"
    echo "Directory $dir in $(pwd) has been deleted."
else
    echo "Directory $dir in $(pwd) does not exist."
fi

#echo "The Current working directory is: $(pwd)"
echo "Making a new $dir directory in $(pwd)"

# Create a new directory named "build"
mkdir "$dir"

echo "Current working directory: $(pwd)"

# Move into the new "build" directory
echo "Moving into the $dir directory in $(pwd)"
cd "$dir" || exit

echo "Created and moved into the new $dir directory."
echo "Current working directory: $(pwd)"
# Run the specified commands

echo "About to run cmake command from $(pwd)"
cmake ../ -DCMAKE_INSTALL_PREFIX=$CONDA_PREFIX
echo "About to run make command from $(pwd)"
make
echo "About to run sudo make install command from $(pwd)"
sudo make install

echo "Finished with brycesTargetCleanerTest.sh script in $(pwd)"
