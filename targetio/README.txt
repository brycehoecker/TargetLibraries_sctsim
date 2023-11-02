1. Build and install
1.1 SVN
$ svn checkout svn+ssh://YOUR_ACCOUNT@svn.in2p3.fr/cta/COM/CCC/TargetIO/trunk TargetIO

1.2 CMake Build
$ mkdir TargetIO_build
$ cd TargetIO_build
$ cmake -G"Eclipse CDT4 - Unix Makefiles" ../ -DPYTHON=ON
$ make
$ sudo make install

1.2.1 Alternativily:
go to build folder and run:
$ccmake <path to trunk>
configure, customise, and generate make files using the "GUI".

1.3 Eclipse support
$ cmake -G"Eclipse CDT4 - Unix Makefiles" ../TargetIO
and import the TargetIO_build directory from your Eclipse as an existing
project.

1.5 Python support
$ cmake ../TargetIO -DPYTHON=ON

Also might need to specify location of the python distribution you wish to use, e.g. -DPYTHON_LIBRARY=/Users/Jason/anaconda3/envs/cta/lib/libpython3.5m.dylib -DPYTHON_INCLUDE_DIR=/Users/Jason/anaconda3/envs/cta/include/python3.5m

If you recieve the error "no image found" when trying to "import target_io" on Mac, try using install_name_tool, e.g. install_name_tool -change libpython3.5m.dylib /Users/Jason/anaconda3/envs/cta/lib/libpython3.5m.dylib /Users/Jason/anaconda3/envs/cta/lib/python3.5/site-packages/_target_io.so

If you recieve the error "no image found" when trying to "import target_io" on Linux, try adding export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib to your .bashrc

1.6 Mac issues.
Make sure that your XCode is up to date and your command line tools are installed using the command:
$xcode-select --install
