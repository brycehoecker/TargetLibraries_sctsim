# Building and installing the TargetCalib software:

To compile the TargetCalib software you will need to have following software installed: 

Dependencies:
	Core:
		cmake version >= 3
		cfitsio
		TargetDriver
		TargetIO
	Python:
		SWIG version >= 3
		numpy

Here follows a short summary of the steps to compile and install the software. More detalied 
steps to install it in a conda enviroment can be found in the next section.

1 create a build directory
2 run cmake in the build directory with the path to the source. 
  The install directory can be set with -DCMAKE_INSTALL_PREFIX
  The TargetDriver and TargetIO software should be installed in the directory pointed by -DCMAKE_INSTALL_PREFIX.
  By default the python module and binaries will be installed under this path with 
  the appropriate folder structure
3 make 
4 make install


Detailed Conda Installation
---------------------------

This guide assumes you will build and install the target software in a conda env.

-Setup a conda env 
	conda create --name myenv
	source activate myenv
-If the system cmake is too old one can install a newer version by
	conda install -c anaconda cmake

-Checkout the TargetCalib software

-Create a build directory outside the source and step into it
	mkdir build
	cd build
-Configure the build
	cmake ../TargetCalib -DCMAKE_INSTALL_PREFIX=$CONDA_PREFIX
-Build and install the target software in your conda env
	make install

In your conda env you can now import all the target software python modules and the exectuables are in your PATH