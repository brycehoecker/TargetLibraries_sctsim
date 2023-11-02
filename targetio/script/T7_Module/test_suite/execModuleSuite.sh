#!/bin/bash

counter=0
args=()
for i in "$@"
do
	args[$counter]=$i
	counter=$counter+1
done

name=${args[0]}
logLevel=${args[1]}
purpose=${args[2]}

python moduleSuite.py $name $logLevel 0 $purpose > fullLog.log 2>&1

checkdir=$HOME/target5and7data/test_suite_output
if [ ! -d "$checkdir" ]; then
	$udata
	$data
fi

cd output

chmod -R 777 *

cd ..




file="tempDir.txt"
while read -r line
do
	echo $line
	testDir=$line
done<"$file"




mkdir -p /Users/tmeures/Pictures/tests/ 
cp $testDir/*.png /Users/tmeures/Pictures/tests/

file="nameFitsDir.txt"
while read -r line
do
	echo $line
	mv $testDir/run*.fits $line/ 
	mv $testDir/run*.log $line/
done<"$file"

file="nameTestDir.txt"
while read -r line
do
	echo $line
	mv $testDir $line/ 
done<"$file"

file="nameFile.txt"
while read -r line
do
	echo $line
	mv fullLog.log $line 
done<"$file"

