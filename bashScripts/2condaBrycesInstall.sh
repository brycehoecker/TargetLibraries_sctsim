#!/bin/bash


#Refresh the environment ?
source ~/.bashrc

anaconda3_install_dir="/home/$USER/anaconda3/"

anaconda3_install_file="/home/$USER/anaconda3/bin/conda"


#how anaconda documentations says to add stuff
eval "$($anaconda3_install_file shell.bash hook)"


#How bryce would add a program to PATH
# Check if the directory exists.
#if [ -d "$anaconda3_install_dir" ]; then
#    # Add the application directory to the PATH if it's not already there.
#    if [[ ":$PATH:" != *":$anaconda3_install_dir:"* ]]; then
#        echo "Adding application to PATH"
#        # Add application directory to PATH for the session.
#        PATH="$PATH:$anaconda3_install_dir"
#        
#        # Add application directory to PATH permanently by appending it to the .bashrc file
#        echo 'export PATH="$PATH:'$anaconda3_install_dir'"' >> ~/.bashrc
#        echo "Application was added to PATH"
#    else
#        echo "Application is already in PATH"
#    fi
#else
#    echo "The specified directory does not exist"
#fi

conda init
conda config --set auto_activate_base false

#Refresh the environment ?
source ~/.bashrc


