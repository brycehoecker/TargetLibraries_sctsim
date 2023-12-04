#!/bin/bash

# Get all directory names in the current directory
#for directory in ./*/
#do
#    # If you need to remove the "./" at the beginning of the directory name,
#    # you can uncomment the following line:
#    # directory=${directory:2}
#
#    # Trim the trailing "/"
#    directory=${directory%*/}
#
#    # Switch to the repository directory
#    cd "$directory" || exit
#
#    # Make a build directory and enter it
#    mkdir build
#    cd build || exit
#
#    # Run your commands
#    #cmake ../ -DCMAKE_INSTALL_PREFIX=$CONDA_PREFIX
#    cmake ../
#    make
#    sudo make install
#
#    # Go back to the root directory before looping to the next repository
#    cd ../../ || exit
#done

##Bryces script to delete all the build folders and remake the targetLibraries
#
#target_dir="build"			#looking for the build directories
#search_word="target"		#that have a parent folder with the search_word
#dirs_to_recreate=()
#
## Check in the current directory
#if [ -d "./${target_dir}" ] && [[ $(basename $(pwd)) == *"${search_word}"* ]]; then
#    echo "Deleting './${target_dir}'..."
#    rm -rf "./${target_dir}"
#    dirs_to_recreate+=("./")
#fi
#
## Check one level deeper
#for dir in ./*/     # list directories in the form "/tmp/dirname/"
#do
#    dir=${dir%*/}      # remove the trailing "/"
#    if [ -d "${dir}/${target_dir}" ] && [[ ${dir} == *"${search_word}"* ]]; then
#        echo "Deleting '${dir}/${target_dir}'..."
#        rm -rf "${dir}/${target_dir}"
#        dirs_to_recreate+=("${dir}")
#    fi
#done
#
## Recreate the directories and run the commands
#for dir in "${dirs_to_recreate[@]}"
#do
#    echo "Recreating '${dir}${target_dir}'..."
#    mkdir "${dir}${target_dir}"
#
#    echo "Running commands in '${dir}${target_dir}'..."
#    cd "${dir}${target_dir}"
#    make
#    sudo make install
#    cd - > /dev/null  # Go back to the previous directory, suppress output
#done
echo "Start of the brycesTargetAutoBuild.sh script. The current working directory is: $(pwd)"

if [ -z "$CONDA_PREFIX" ]; then
	echo -e "\e[31m         !!!!!ERROR!!!!!\e[0m"
    echo -e "\e[31m   No Conda environment is active.\e[0m"
    echo -e "\e[31m Please activate a conda environment and re-run the script.\e[0m"
else
    echo -e "\e[32mA Conda environment is active. The path to the environment is $CONDA_PREFIX.\e[0m"

	# ask the user for the script name
	#echo -n "Enter script name to search for: "
	#read script_name
	script_name="brycesTargetBuilder.sh"
	# search for the scripts in the current directory and one level down and store them in an array
	echo "Searching for scripts named $script_name"
	script_list=()
	while IFS=  read -r -d $'\0'; do
		script_list+=("$REPLY")
	done < <(find . -maxdepth 2 -name $script_name -print0)

	# if no scripts are found, exit the script
	if [ ${#script_list[@]} -eq 0 ]; then
		echo -e "\e[31mNo scripts found\e[0m"
		exit 1
	fi

	# show the user the list of parent folders
	echo "List of parent folders for the scripts found:"
	for index in ${!script_list[*]}
	do
		script_dir=$(dirname "${script_list[$index]}")
		echo "[$index] $script_dir"
	done

	# ask the user to specify the order to run the scripts
	echo "Please specify the order to run the scripts (use space-separated indices):"
	read -a order

	# validate the order
	for index in ${order[@]}
	do
		if [ "$index" -lt 0 ] || [ "$index" -ge ${#script_list[@]} ]; then
			echo -e "\e[31mInvalid index: $index\e[0m"
			exit 1
		fi
	done
	# execute the scripts in the order specified by the user
	#echo "Current working directory: $(pwd)"
	echo "Now Running all the found scripts."

	#for index in ${order[@]}
	#do
	#    echo "Current working directory: $(pwd)"
	#    script="${script_list[$index]}"
	#    if [ -x "$script" ]
	#    then
	#		echo "Current working directory: $(pwd)"
	#        echo "Running script: $script"
	#        ./"$script"
	#    else
	#        echo "The script $script does not have execute permissions. Skipping..."
	#    fi
	#done

	# execute the scripts in the order specified by the user
	for index in ${order[@]}
	do
		echo "Current working directory: $(pwd)"
		script="${script_list[$index]}"
		if [ -x "$script" ]
		then
			script_dir=$(dirname "${script}")
			echo "Changing directory to: $script_dir"
			cd "$script_dir"
			script_base=$(basename "${script}")
			echo "Running script: $script_base"
			./"$script_base"
			cd - > /dev/null  # Go back to the previous directory
		else
			echo "The script $script does not have execute permissions. Attempting to add them..."
			chmod +x "$script"
			if [ $? -eq 0 ]; then
				script_dir=$(dirname "${script}")
				echo "Changing directory to: $script_dir"
				cd "$script_dir"
				script_base=$(basename "${script}")
				echo "Running script: $script_base"
				./"$script_base"
				echo "Finished Running: $script_base , exiting."
				cd - > /dev/null  # Go back to the previous directory
			else
				echo -e "\e[31m!!!!!ERROR!!!!!ERROR!!!!!ERROR!!!!!ERROR!!!!!ERROR!!!!!ERROR!!!!!ERROR!!!!!ERROR!!!!!\e[0m"
				echo -e "\e[31m~~~~~~~~~~~~~~Unable to add execute permissions to the script. Skipping~~~~~~~~~~~~~~\e[0m"
				#echo "!!!!!ERROR!!!!!ERROR!!!!!ERROR!!!!!ERROR!!!!!ERROR!!!!!ERROR!!!!!ERROR!!!!!ERROR!!!!!"
			fi
		fi
	done
	echo "Finished running all $script scripts. Now exiting, Goodbye!"
fi
