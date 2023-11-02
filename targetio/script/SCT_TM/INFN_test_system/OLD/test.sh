#!/bin/bash -i

#colors for text
RED="\e[0;31m"
GREEN="\e[0;32m"
NC="\033[0m" # No Color

#number of module required as a parameter
if [ $# -ne 1 ]
then
  echo -e "${RED}FATAL: illegal number of arguments.${NC}"
  echo -e "${RED}usage: $0 <serial number of module>.${NC}"
  exit 1
fi

MODULE=$1

#check that MODULE is a number
re='^[0-9]+$'
if ! [[ $MODULE =~ $re ]] ; then
   echo "${RED}FATAL: serial number must be numeric.${NC}" >&2; exit 1
fi

#default tag
TAG=test20200116_sh

#pulse amplitude as commanded to the function generator, for the first signal run
PULSE_AMPLITUDE_VOLTS=1 #pulse amplitude
PULSE_AMPLITUDE_VOLTS_TRIGGERSCAN_PMTREF4=0.1 #pulse amplitude used for trigger rate scan over PMTRef4 parameter
PULSE_AMPLITUDE_VOLTS_TRIGGERSCAN_THRESH=0.05 #pulse amplitude used for trigger rate scan over "thresh" parameter
PULSE_FREQUENCY=1113 #commanded pulse frequency to the function generator
DEFAULT_VPED=1200 #default VPED to be used
TRIGGERSCAN_PMTREF4_STEPSIZE=10 #stepsize for triggerscan over "PMTRef4" parameter
TRIGGERSCAN_THRESH_STEPSIZE=20 #stepsize for trigger rate scan over "thresh" parameter
ENABLE_PEDESTAL=0
ENABLE_SIGNAL=0
ENABLE_LINEARITY=0
ENABLE_VPED_SCAN=0

result=0 #0 means success

for i in 1 # for loop run just once, in order to use "break" statement
do

  time { #this line is used to time the code block enclosed between the curly braces

    if [ "$ENABLE_PEDESTAL" -eq "1" ]; then
      #turn off the arbitrary function generator
      LASTCOMMAND=./agilent33250A_off.py; $LASTCOMMAND; result=$?
      if [ $result -ne 0 ]; then break; fi
      LASTCOMMAND=./run_pedestal.py; $LASTCOMMAND -m ${MODULE} -mt ${TAG} -b 8 -p 8 -l 5 -d 450 -t 2 -vp ${DEFAULT_VPED}; result=$?
      if [ $result -ne 0 ]; then break; fi
    fi


    if [ "$ENABLE_SIGNAL" -eq "1" ]; then
      #turn on the function generator and output a certain pulse amplitude and frequency
      LASTCOMMAND=./agilent33250A_inverted.py; $LASTCOMMAND ${PULSE_AMPLITUDE_VOLTS} ${PULSE_FREQUENCY}; result=$?
      if [ $? -ne 0 ]; then break; fi
      #run a signal test with the selected pulse amplitude
      LASTCOMMAND=./run_signal.py; $LASTCOMMAND -m ${MODULE} -mt ${TAG} -b 8 -p 8 -l 3 -d 450 -t 1 -vp ${DEFAULT_VPED}  -o test1; result=$?
      if [ $? -ne 0 ]; then break; fi
    fi

    if [ "$ENABLE_LINEARITY" -eq "1" ]; then
      #run signal test with different amplitures (linearity scan)
      LASTCOMMAND=./run_signal.py; $LASTCOMMAND -m ${MODULE} -mt ${TAG} -b 8 -p 8 -l 3 -d 450 -t 1 -vp ${DEFAULT_VPED} -o amplitude_test -s --signalfreq ${PULSE_FREQUENCY} --signalvals 0.1 4.2 0.2; result=$?
      if [ $? -ne 0 ]; then break; fi
    fi

    if [ "$ENABLE_VPED_SCAN" -eq "1" ]; then
      #run several pededstal aquisitions  for different VPED values
      LASTCOMMAND=./run_pedestal.py; $LASTCOMMAND -m ${MODULE} -mt ${TAG} -b 8 -p 8 -l 5 -d 450 -t 2 -vp ${DEFAULT_VPED} -v --vpedvals 1000 4100 500; result=$?
      if [ $? -ne 0 ]; then break; fi
    fi


    #set the pulse amplitude for the trigger rate scan over PMTRef4 parameter
    LASTCOMMAND=./agilent33250A_inverted.py; $LASTCOMMAND ${PULSE_AMPLITUDE_VOLTS_TRIGGERSCAN_PMTREF4} ${PULSE_FREQUENCY}; result=$?
    if [ $? -ne 0 ]; then break; break; fi

    #trigger rate scan over PMTRef4 values
    LASTCOMMAND=./run_triggerscan.py; $LASTCOMMAND -m ${MODULE} -mt ${TAG} --pmtref4vals 0 4096 ${TRIGGERSCAN_PMTREF4_STEPSIZE} -gr 0 15; result=$?
    if [ $? -ne 0 ]; then break; fi

    #set the pulse amplitude for the trigger rate scan over the thresh parameter
    LASTCOMMAND=./agilent33250A_inverted.py; $LASTCOMMAND ${PULSE_AMPLITUDE_VOLTS_TRIGGERSCAN_THRESH} ${PULSE_FREQUENCY}; result=$?
    if [ $? -ne 0 ]; then break; fi

    #trigger rate scan over the thresh parameter
    LASTCOMMAND=./run_triggerscan.py; $LASTCOMMAND -m ${MODULE} -mt ${TAG} --threshvals 0 4096 ${TRIGGERSCAN_THRESH_STEPSIZE} -gr 0 15; result=$?
    if [ $? -ne 0 ]; then break; fi

  } #time clause

done #for clause


printf "Overall analysis status: ";
  if [ $result -eq 0 ]; then echo -e "\e[0;32mSUCCESS\e[0m"; else
    echo -e "\e[0;31mFAILURE\e[0m";
    echo -e "Failing command: ${RED}${LASTCOMMAND}${NC}"
    exit 1
  fi


#note: currently the system is left in a "bad state" after run_triggercan (run_signal fails if lanched afterwards)
#workaround: moved run_triggerscan to the end of the test



