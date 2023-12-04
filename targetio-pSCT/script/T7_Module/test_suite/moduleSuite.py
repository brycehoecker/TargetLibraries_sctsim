#!/usr/bin/env python

import tuneModule
import getSerial
import sqlSetTrimTest
import runInit
import LEDPulseWFs
import powerCycle
import lowSideLoopTD
import breakDownScan
import triggerThresh
import pickThresh
import time
import datetime
import run_control
import os, sys
import analyzeLowSideLoop
import prepareLog
import csv
import analyzeTriggerThreshScan
import plot_waves
import noiseTriggers
import numpy as np

lowSideLoop=1
threshScan=1
breakDown=0
internalTrigger=1
externalTrigger=1
softwareTrigger=1

def refreshFile(inFile, inFileName):
	inFile.close()
	inFile = open(inFileName,'a+')
	return inFile	

argList = sys.argv

print argList

name = None
purpose = "General test."
logLevel = None
emailAddress = None


outputDir = "output/"
try:
	os.mkdir (outputDir)
except:
	print "Output-directory already exists."

#try:
#	os.mkdir('{}/logs'.format(outputDir))
#	os.mkdir('{}/images'.format(outputDir))
#except:
#	print "Image and log directories already exist."


if(len(argList)<4):
	print "Not enough input arguments!"
	name = None
	logLevel = None
	logToFile= -1
	purpose = None
else:
	name = argList[1]
#	purpose = argList[2]
	logLevel = int(argList[2])
	logToFile = int(argList[3])
	purpose = " ".join(str(x) for x in argList[4:len(argList)])

	print "The purpose:", purpose
print "Todo: Read all registers and dump info into logFile."
print "Todo: move necessary files into common location! Brickpowersupply, Keithley, ..."
try:
	os.remove("/Users/colinadams/Google Drive/documentation_testsuite/report.csv")
except:
	print "tried to remove report.csv prior to creating it, but it wasn't found"
csvout = open("/Users/colinadams/Google Drive/documentation_testsuite/report.csv","w")
try:
	os.chmod("/Users/colinadams/Google Drive/documentation_testsuite/report.csv", 0o777)
except:
	print "Check Google Drive file permissions after running"
wr = csv.writer(csvout)
report = []

moduleID,FPM = getSerial.getSerial()
#moduleID = 123
#FPM=[4,6]


moduleID = int(moduleID)

numBlock=2



#Initialize looging and produce neede file outputs.
dataset, testDir, assocRun, assocFile, moduleID, FPM, purpose, user, logFileName, testDirFinal, fitsDir = prepareLog.prepareLog(moduleID, FPM, name, purpose, logLevel, logToFile, outputDir)
##dataset = "20160713_0736"

nameFile = open("nameFile.txt", 'w')
nameFile.write(" %s   \n" % logFileName)
nameFile.close()

nameFile = open("nameTestDir.txt", 'w')
nameFile.write(" %s   \n" % testDirFinal)
nameFile.close()

nameFile = open("nameFitsDir.txt", 'w')
nameFile.write(" %s   \n" % fitsDir)
nameFile.close()

nameFile = open("tempDir.txt", 'w')
nameFile.write(" %s   \n" % testDir)
nameFile.close()


report.extend([dataset,moduleID,FPM,purpose])

#original_stdout =  sys.stdout
#sys.stdout = logFile 

runListFile = open(assocRun,'w')
fileListFile = open(assocFile,'w')



#Begin power cycle
bps = powerCycle.powerCycle()



#Begin initialization
module, tester = runInit.Init()
Vped = 1106

firstRun=0

if(lowSideLoop):

	#Begin lowside 
	outRunList, outFileList = lowSideLoopTD.recordModule(module, outputDir=testDir)
	runListFile.write("lowSideLoop\n")
	fileListFile.write("lowSideLoop\n")
	runListFile = refreshFile(runListFile, assocRun)
	fileListFile = refreshFile(fileListFile, assocFile)
	for i in outRunList:
		runListFile.write("%d\n" % i)
	for i in outFileList:
		fileListFile.write("%s\n" % i)


	runListFile = refreshFile(runListFile, assocRun)
	fileListFile = refreshFile(fileListFile, assocFile)



	if(firstRun==0): firstRun = outRunList[0]
	lastLoopRun = outRunList[-1]

	lowSideRuns = [firstRun, lastLoopRun]

	#Analyze low side loop
	analyzeLowSideLoop.analyzeLowSideLoop(testDir, dataset, runList=lowSideRuns)



#Begin tuning


Vped = 1106
tuneModule.getTunedWrite(moduleID,FPM,module,Vped, numBlock=numBlock)

deadTimeList=[7500,12500,50000] #formerly [500, 5000, 15000]
freq = 100
if(threshScan):
	runListFile.write("threshScan\n")
	fileListFile.write("threshScan\n")
	runListFile = refreshFile(runListFile, assocRun)
	fileListFile = refreshFile(fileListFile, assocFile)
	#Run a threshold scan
	
	triggerON=1
	for deadTime in deadTimeList:
	   for asic in range(4):
		for group in range(4):
			print "FIXME: For now the system has to be power-cycled every time after one trigger group!"
			print "FIXME: Somehow register writing gets corrupted after a while when both"
			print "FIXME: EnableTriggerCounterContribution and EnableTrigger are true. If one of them is used "
			print "FIXME: separately, everything runs fine. We might have to put in a redmine issue."
			trigThreshDone = False
			trigThreshCounter = 0
			while not trigThreshDone and trigThreshCounter < 2:
				outRunList, outFileList,trigThreshDone = triggerThresh.trigThreshScan(module, tester, moduleID, asic, group, dataset, testDir, deadtime=deadTime, inputf=freq, enableReadout=triggerON)
				runInit.Close(module,tester)
				bps = powerCycle.powerCycle()
				module, tester = runInit.Init()
				tuneModule.getTunedWrite(moduleID,FPM,module,Vped, numBlock=numBlock)
				for i in outRunList:
					runListFile.write("%d\n" % i)
					if(firstRun==0): firstRun = outRunList[0]
				for i in outFileList:
					fileListFile.write("%s\n" % i)
				runListFile = refreshFile(runListFile, assocRun)
				fileListFile = refreshFile(fileListFile, assocFile)
				trigThreshCounter += 1
	
	#Run without actual trigger: This avoids interference of data readout with triggering.
	deadTime=12500
	triggerON=0
	for asic in range(4):
		for group in range(4):
			print "FIXME: For now the system has to be power-cycled every time after one trigger group!"
			print "FIXME: Somehow register writing gets corrupted after a while when both"
			print "FIXME: EnableTriggerCounterContribution and EnableTrigger are true. If one of them is used "
			print "FIXME: separately, everything runs fine. We might have to put in a redmine issue."
			trigThreshDone = False
			trigThreshCounter = 0
			while not trigThreshDone and trigThreshCounter < 2:
				outRunList, outFileList,trigThreshDone = triggerThresh.trigThreshScan(module, tester, moduleID, asic, group, dataset, testDir, deadtime=deadTime, inputf=freq, enableReadout=triggerON)
				runInit.Close(module,tester)
				bps = powerCycle.powerCycle()
				module, tester = runInit.Init()
				tuneModule.getTunedWrite(moduleID,FPM,module,Vped, numBlock=numBlock)
				for i in outRunList:
					runListFile.write("%d\n" % i)
					if(firstRun==0): firstRun = outRunList[0]
				for i in outFileList:
					fileListFile.write("%s\n" % i)
				runListFile = refreshFile(runListFile, assocRun)
				fileListFile = refreshFile(fileListFile, assocFile)
				trigThreshCounter += 1
	
	analyzeTriggerThreshScan.analyzeThreshScan(dataset, testDir, deadTimeList, freq)



deadtime4readout = deadTimeList[1]
#finds a conservative Thresh value for each trigger pixel in the module
#consThresh, messedUpPick, aggrThresh = pickThresh.pickThresh(testDir, testDirFinal, deadtime=deadtime4readout, triggerEN=0)

#print "Pick thresh output"
#print consThresh
#print aggrThresh


if(breakDown):

	#Begin lowside 
	outRunList, outFileList = breakDownScan.recordModule(module, tester=tester, testDir=testDir, outputDir=testDir, dataset=dataset)
	runListFile.write("BreakDownScan\n")
	fileListFile.write("BreakDownScan\n")
	runListFile = refreshFile(runListFile, assocRun)
	fileListFile = refreshFile(fileListFile, assocFile)
	for i in outRunList:
		runListFile.write("%d\n" % i)
	for i in outFileList:
		fileListFile.write("%s\n" % i)


	runListFile = refreshFile(runListFile, assocRun)
	fileListFile = refreshFile(fileListFile, assocFile)



	if(firstRun==0): firstRun = outRunList[0]
	lastLoopRun = outRunList[-1]

	breakDownScan_runs = [firstRun, lastLoopRun]

	#Analyze low side loop
#	analyzeLowSideLoop.analyzeLowSideLoop(testDir, dataset, runList=lowSideRuns)


runInit.Close(module,tester)
bps = powerCycle.powerCycle()
module, tester = runInit.Init()
tuneModule.getTunedWrite(moduleID,FPM,module,Vped, numBlock=numBlock)

consThresh, messedUpPick, aggrThresh = pickThresh.pickThresh(testDir, testDirFinal, deadtime=deadtime4readout, triggerEN=1)
#sometimes the last thresh scan may not have had the trigger readout enabled, this will allow it to continue with data taken with the trigger readout disabled
if not consThresh:
	consThresh, messedUpPick, aggrThresh = pickThresh.pickThresh(testDir, testDirFinal, deadtime=deadtime4readout, triggerEN=0)
#print consThresh
#print aggrThresh


frequency = 1000


#Begin LED Flasher Test with internal trigger
if(internalTrigger):
	trigger = 1
	runDuration=3
	for j in range(0,16):
	
		outRunList, outFileList = LEDPulseWFs.LEDPulseWaveforms(tester,module,frequency,trigger,runDuration, groupList=[j], thresh=consThresh, outputDir=testDir)
		runListFile.write("Flasher with internal trigger, group: %d\n" % j)
		fileListFile.write("Flasher with internal trigger, group: %d\n" % j)
		runListFile = refreshFile(runListFile, assocRun)
		fileListFile = refreshFile(fileListFile, assocFile)
		runListFile.write("%d\n" % outRunList[0])
		fileListFile.write("%s\n" % outFileList[0])
		runListFile = refreshFile(runListFile, assocRun)
		fileListFile = refreshFile(fileListFile, assocFile)
	
		plot_waves.plot_events(outRunList, testDir, dataset, group=j)


#Begin noise test with internal trigger
	trigger = 3
	runDuration = 10
	for j in range(0,16):
		outRunList, outFileList = LEDPulseWFs.LEDPulseWaveforms(tester,module,frequency,trigger,runDuration, groupList=[j],thresh=consThresh, outputDir=testDir)
		runListFile.write("Noise with internal trigger, group: %d\n" % j)
		fileListFile.write("Noise with internal trigger, group: %d\n" % j)
		runListFile = refreshFile(runListFile, assocRun)
		fileListFile = refreshFile(fileListFile, assocFile)
		runListFile.write("%d\n" % outRunList[0])
		fileListFile.write("%s\n" % outFileList[0])
		runListFile = refreshFile(runListFile, assocRun)
		fileListFile = refreshFile(fileListFile, assocFile)
		plot_waves.plot_events(outRunList, testDir, dataset, group=j)

	#noise test with all groups enabled for triggering
	allGroups = np.arange(16)
	outRunList, outFileList = LEDPulseWFs.LEDPulseWaveforms(tester,module,frequency,trigger,runDuration, groupList=allGroups,thresh=consThresh, outputDir=testDir)
	runListFile.write("Noise with internal trigger, all groups\n")
	fileListFile.write("Noise with internal trigger, all groups\n")
	runListFile = refreshFile(runListFile, assocRun)
	fileListFile = refreshFile(fileListFile, assocFile)
	runListFile.write("%d\n" % outRunList[0])
	fileListFile.write("%s\n" % outFileList[0])
	runListFile = refreshFile(runListFile, assocRun)
	fileListFile = refreshFile(fileListFile, assocFile)
	plot_waves.plot_events(outRunList, testDir, dataset, group="ALL")

	#plotting noise from each enabled group
	noiseRuns = noiseTriggers.getNoiseRuns(runListFile)
	noiseTriggers.plotNoiseTriggers(noiseRuns, testDir, dataset)

#start taking data with software triggers
if(softwareTrigger):
	trigger = 9
	runDuration = 10
	outRunList, outFileList = LEDPulseWFs.LEDPulseWaveforms(tester,module,frequency,trigger,runDuration,thresh=consThresh, outputDir=testDir)
	if(firstRun==0): firstRun = outRunList[0]
	runListFile.write("Software trigger\n")
	fileListFile.write("Software trigger\n")
	runListFile = refreshFile(runListFile, assocRun)
	fileListFile = refreshFile(fileListFile, assocFile)
	for i in outRunList:
		runListFile.write("%d\n" % i)
	for i in outFileList:
		fileListFile.write("%s\n" % i)
	runListFile = refreshFile(runListFile, assocRun)
	fileListFile = refreshFile(fileListFile, assocFile)
	
	plot_waves.plot_events(outRunList, testDir, dataset)

#Begin noise test with external trigger
if(externalTrigger):
	trigger = 0
	runDuration = 2
	outRunList, outFileList = LEDPulseWFs.LEDPulseWaveforms(tester,module,frequency,trigger,runDuration, numBlock=numBlock, triggerDly=93, outputDir=testDir)
	runListFile.write("Noise with external trigger\n")
	fileListFile.write("Noise with external trigger\n")
	runListFile = refreshFile(runListFile, assocRun)
	fileListFile = refreshFile(fileListFile, assocFile)
	runListFile.write("%d\n" % outRunList[0])
	fileListFile.write("%s\n" % outFileList[0])
	runListFile = refreshFile(runListFile, assocRun)
	fileListFile = refreshFile(fileListFile, assocFile)
	plot_waves.plot_events(outRunList, testDir, dataset, group='EXT')

	



#Begin LED Flasher Test with external trigger
#	runInit.Close(module,tester)
#	bps = powerCycle.powerCycle()
#	module, tester = runInit.Init()
#	tuneModule.getTunedWrite(moduleID,module,Vped)	
	trigger = 2
	runDuration = 2
	outRunList, outFileList = LEDPulseWFs.LEDPulseWaveforms(tester,module,frequency,trigger,runDuration, numBlock=numBlock, triggerDly=93, outputDir=testDir)
	if(firstRun==0): firstRun = outRunList[0]
	runListFile.write("Flasher with external trigger\n")
	fileListFile.write("Flasher with external trigger\n")
	runListFile = refreshFile(runListFile, assocRun)
	fileListFile = refreshFile(fileListFile, assocFile)
	runListFile.write("%d\n" % outRunList[0])
	fileListFile.write("%s\n" % outFileList[0])
	runListFile = refreshFile(runListFile, assocRun)
	fileListFile = refreshFile(fileListFile, assocFile)
	
	plot_waves.plot_events(outRunList, testDir, dataset,group='EXT')




try:
	lastRun = outRunList[-1]
except:
	lastRun = firstRun

report.extend([firstRun,lastRun,None,None,None,None,None,None,None,None,None,user])
wr.writerow(report)
csvout.close()

runInit.Close(module, tester)

powerCycle.powerOff(bps)

runListFile.close()
fileListFile.close()

if messedUpPick:
	print "Pick thresh might have failed, check log section to see what went wrong"

print "Suite finished"



