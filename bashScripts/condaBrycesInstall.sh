#!/bin/bash

# Make sure only root can run our script
#if [ "$(id -u)" != "0" ]; then
#   echo "This script must be run as root" 1>&2
#   exit 1
#fi

#Enables EPEL libraries (Extra Packages for Enterprise Linux)
#dnf config-manager --enable crb
#dnf install epel-release -y

# Read the file line by line
#while IFS= read -r package
#do
#    # Install the package
#    sudo dnf install -y "$package"
#done < packages.txt


# Define the download directory
download_dir=~/Downloads/	#Does not work when using sudo
#userhome_dir=~/				#user home directory

#If the user runs using sudo, the files download to the root directory
#download_dir="/home/${SUDO_USER:-$USER}/Downloads/"

# Download files from the wget_install list DOES NOT CHECK IF FILE IS ALREADY DOWNLOADED
#while IFS= read -r wget_install
#do
#    # Download the file
#    wget -P "$download_dir" "$wget_install"
#done < wget_install.list


# Read the file line by line
while IFS= read -r wget_install
do
    # Extract the filename from the URL inside wget_install.list
    file_name=$(basename "$wget_install")
    
    # Check if the file already exists in the download directory
    if [ ! -f "${download_dir}${file_name}" ]; then
        # Download the file if it doesn't already exist
        wget -P "$download_dir" "$wget_install"
    else
        echo "File $file_name already exists, skipping download."
    fi
done < wget_install.list





############install the anaconda version Anaconda2-2019.07-Linux-x86 64.sh#####################

#Use this instead if you want user to pick where to manually install the anaconda directories
#"${download_dir}Anaconda2-2019.07-Linux-x86_64.sh"

#anaconda2_dir="/home/${SUDO_USER:-$USER}/anaconda2/"
#chmod +x "${download_dir}Anaconda2-2019.07-Linux-x86_64.sh"
#"${download_dir}Anaconda2-2019.07-Linux-x86_64.sh" -b -p $anaconda2_dir -t
#-b agrees to license without confirmation, -p installs prefix, -t tests install
#HOWEVER -b does not make PATH modifications to ~/.bashrc and does not edit the .bashrc or .bash_profile files
#You would have to make those changes yourself with something like 
#eval "$(anaconda2_dir shell.bash hook)"

#Initialize the conda environment
#conda init
#conda config --set auto_activate_base false

###############################################################################################

############install the anaconda version Anaconda3-2023.03-1-Linux-x86_64.sh###################
#
#anaconda3_install_dir="/home/$USER/anaconda3/"
# Make the downloaded script executable and run it
#chmod +x "${download_dir}Anaconda3-2023.03-1-Linux-x86_64.sh"
#"${download_dir}Anaconda3-2023.03-1-Linux-x86_64.sh" -b -p $anaconda3_install_dir -t
#"${download_dir}Anaconda3-2023.03-1-Linux-x86_64.sh" -help #opens help menu

###############################################################################################


############install the anaconda version Anaconda3-2019.07-Linux-x86_64.sh###################

anaconda3_install_dir="/home/$USER/anaconda3/"
# Make the downloaded script executable and run it
chmod +x "${download_dir}Anaconda3-2019.07-Linux-x86_64.sh"
"${download_dir}Anaconda3-2019.07-Linux-x86_64.sh" -b -p $anaconda3_install_dir -t
#"${download_dir}Anaconda3-2019.07-Linux-x86_64.sh" -help #opens help menu

###############################################################################################














