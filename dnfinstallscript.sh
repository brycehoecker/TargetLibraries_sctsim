#!/bin/bash

# File containing the list of packages
PACKAGE_LIST="dnfinstall.list"

# Checking if the package list file exists
if [ ! -f "$PACKAGE_LIST" ]; then
    echo "Package list file not found: $PACKAGE_LIST"
    exit 1
fi

# Creating an array to hold the package names
declare -a packages

# Reading each line in the file and adding it to the array
while IFS= read -r package; do
    packages+=("$package")
done < "$PACKAGE_LIST"

# Updating the package repository
echo "Updating package repository..."
sudo dnf check-update

# Installing all packages in the array
echo "Installing packages..."
sudo dnf install -y "${packages[@]}"

echo "All packages installed successfully."
