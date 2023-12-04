
#!/bin/bash

read -p "Insert your name: " name
echo "The name is: " $name


read -p "Insert purpose of this test: " purpose

read -p "Choose logLevel (0=Error, 1=Warning, 2=Info, 3=Debug): " logLevel


echo "Program is run as nohup. Use >tail -f fullLog.log, to follow the log messages. At the end, this file will be used into the test directory."

nohup bash execModuleSuite.sh $name $logLevel "$purpose" &
