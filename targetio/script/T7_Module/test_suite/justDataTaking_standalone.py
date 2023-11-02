#!/usr/bin/env python

import tuneModule
import runInit_standalone
import LEDPulseWFs_standalone
import lowSideLoopTD
import triggerThresh
import pickThresh
import powerCycle
import time
import datetime
import run_control
import os, sys
import analyzeLowSideLoop
import prepareLog
import csv
import analyzeTriggerThreshScan
import plot_waves

internalTrigger=1
syncTrigger=0
externalTrigger=0

##outputDir = "/Users/tmeures/test_suite/output_photon/"
outputDir = "/Users/ltaylor/target5and7data/"
try:
	os.mkdir (outputDir)
except:
	print "Output-directory already exists."

testDir = outputDir

logFormat = "%(module)s :: %(funcName)s : %(msecs)d : %(message)s"
##logging.basicConfig(format=logFormat, level=logging.DEBUG)

#moduleID,FPM = getSerial.getSerial()
moduleID=int(110)
FPM=[4,12]


#Begin power cycle
bps = powerCycle.powerCycle()
time.sleep(2)

frequency=100

#Begin initialization
#module, tester = runInit_standalone.Init()
module = runInit_standalone.Init()
Vped = 1106

for Nasic in range(4):
	module.WriteASICSetting("WR_ADDR_Incr1LE_Delay", Nasic, 3) # Incr1 start
	module.WriteASICSetting("WR_ADDR_Incr1TE_Delay", Nasic, 18) # Incr1 end
	module.WriteASICSetting("WR_STRB1LE_Delay", Nasic, 32) # STRB1 start
	module.WriteASICSetting("WR_STRB1TE_Delay", Nasic, 39) # STRB1 end
	module.WriteASICSetting("WR_ADDR_Incr2LE_Delay", Nasic, 35) # Incr2 start
	module.WriteASICSetting("WR_ADDR_Incr2TE_Delay", Nasic, 50) # Incr2 end
	module.WriteASICSetting("WR_STRB2LE_Delay", Nasic, 0) # STRB2 start
	module.WriteASICSetting("WR_STRB2TE_Delay", Nasic, 7) # STRB2 end
	module.WriteASICSetting("SSPinLE_Delay", Nasic, 50) # SSPin start
	module.WriteASICSetting("SSPinTE_Delay", Nasic, 3)  # SSPin end

if(internalTrigger):
	trigger = 1
	runDuration=3
	#consThresh, messedUpPick = pickThresh.pickThresh(testDir, testDirFinal, deadtime=12500)
	consThresh = 300 #FIXME
	print "Pick thresh output"
	print consThresh
	for j in range(0,16):
	
		outRunList, outFileList = LEDPulseWFs_standalone.LEDPulseWaveforms(module,frequency,trigger,runDuration, groupList=[j], thresh=consThresh, outputDir=outputDir)


Vped = 1106
numBlock=4	
delay=700
if(syncTrigger):
	tuneModule.getTunedWrite(moduleID, FPM, module,Vped, numBlock=numBlock)
	trigger = 2
	runDuration = 2
	outRunList, outFileList = LEDPulseWFs_standalone.LEDPulseWaveforms(module,frequency,trigger,runDuration, numBlock=numBlock, triggerDly=delay, outputDir=outputDir)

if(externalTrigger):
	tuneModule.getTunedWrite(moduleID, FPM, module,Vped, numBlock=numBlock)
	trigger = 0
	runDuration = 2
	outRunList, outFileList = LEDPulseWFs_standalone.LEDPulseWaveforms(module,frequency,trigger,runDuration, numBlock=numBlock, triggerDly=delay, outputDir=outputDir)

###raw_input("Press enter to end the program.")
#runInit_standalone.Close(module, tester)
runInit_standalone.Close(module)
powerCycle.powerOff(bps)

print "Suite finished"



