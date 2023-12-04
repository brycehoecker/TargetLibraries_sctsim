#!/usr/bin/env python

import tuneModule
#import getSerial
#import sqlSetTrimTest
import runInit
import LED
import LEDPulseWFs
import target_io
import target_driver
#import powerCycle
#import lowSideLoopTD
#import triggerThresh
import pickThresh
import time
import datetime
import run_control
import os, sys
#import analyzeLowSideLoop
import prepareLog
import csv
#import analyzeTriggerThreshScan
#import plot_waves
import logging
import piCom
import datetime
import serial
import ConfigParser
import json

internalTrigger=0
externalTrigger=0
softwareTrigger=1
#threshScan=1

def refreshFile(inFile, inFileName):
	inFile.close()
	inFile = open(inFileName,'a')
	return inFile	

argList = sys.argv

print argList

name = None
purpose = "General test."
logLevel = None
emailAddress = None


##outputDir = "/Users/tmeures/test_suite/output_photon/"
outputDir = "/home/ctauser/target5and7data/"
#outputDir = "output/"
try:
	os.mkdir (outputDir)
except:
	print "Output-directory already exists."

testDir = outputDir

if(len(argList)<4):
	print "Not enough input arguments!"
	name = "General"
	logLevel = 3
	logToFile= 0
	purpose = "test"
else:
	name = argList[1]
#	purpose = argList[2]
	logLevel = int(argList[2])
	logToFile = int(argList[3])
	purpose = " ".join(str(x) for x in argList[4:len(argList)])

#moduleID,FPM = getSerial.getSerial()
#FPM=[4,2]

logFormat = "%(module)s :: %(funcName)s : %(msecs)d : %(message)s"
logging.basicConfig(format=logFormat, level=logging.DEBUG)

config = ConfigParser.ConfigParser()
config.read('./config/default.ini')

#Initialize looging and produce neede file outputs.
###dataset, testDir, assocRun, assocFile, moduleID, FPM, purpose, user, logFileName, testDirFinal, fitsDir = prepareLog.prepareLog(moduleID, FPM, name, purpose, logLevel, logToFile, outputDir)
##dataset = "20160713_0736"

#original_stdout =  sys.stdout
#sys.stdout = logFile 


timestamp = time.time()
dataset = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M')
rateTestOut='{}/bp_ratetest/{}.csv'.format(outputDir,dataset)
assocRun = "runList.txt"
assocFile = "fileList.txt"

runListFile = open(assocRun,'w')
fileListFile = open(assocFile,'w')

ld =LED.LED()
try:
	ld.setLED(100,0,0)
except:
	logging.warning("LED pulser not responding!")


#Begin power cycle
#bps = powerCycle.powerCycle()
baseIP=["192.168.10.", "192.168.12."]
moduleIP_dict={100:"81",101:"89", 107:"64", 108:"180", 110:"101", 111:"127", 112:"36", 113:"21", 114:"157", 115:"247", 116:"247", 118:"45", 119:"130", 121:"229", 123:"109", 124:"114", 125:"122", 126:"188", 128:"131"}
std_my_ip=["192.168.10.1", "192.168.12.1"]
DACQ_dict={100:1, 101:2, 107:1, 108:1, 110:2, 111:1, 112:1, 113:1, 114:1, 115:1, 116:1, 118:1, 119:1, 121:1, 123:1, 124:1, 125:2, 126:2, 128:1}
#moduleIDList=[0,i1,2,3]


#The module distribution inside the camera:
#********** 118  125  126  101 *************
#********** 119  108  121  110 *************
#********** 128  123  124  112 *************
#********** 100  111  114  107 *************



#Which modules we want to run:
ourModuleIDList=json.loads(config.get("main","modules")) #[118, 119, 108, 121, 128, 123, 124, 112, 100, 111, 114, 107]  ##[118, 125, 126, 101, 119, 108, 121, 110, 128, 123, 124, 112, 100, 111, 114, 107]  #[119, 108, 116, 128, 123, 124, 112, 111, 114, 107] 
moduleIDList=range(len(ourModuleIDList))
#What Vped to use:
VpedList = [1106]*len(ourModuleIDList)


#Set these parameters:
triggerModule=config.get("main","triggerModule")
runDuration = config.get("main","runDuration")  #in seconds
numberOfRuns = config.get("main","numberOfRuns")
HV=config.get("main","HV")   #(1=ON, 0=OFF)
numBlock=config.get("main","numBlock")

#For threshold scan:
threshScan=config.get("threshscan","threshScan")
asicList=json.loads(config.get("threshscan","asicList"))
groupList=json.loads(config.get("threshscan","groupList"))

#For datataking:
dataTaking=config.get("datataking","dataTaking")
base_thresh=config.get("datataking","base_thresh")
delay=config.get("datataking","delay")    ###648 #666

#LED flahser:
fastLEDFlasherON=config.get("datataking","fastLEDFlasherON")

#Special functions:
changeVped=0
VpedChange=5


#Run data taking/threshScan, etc...
changePackDelay=0
defaultSep = 0		#boolean, chooses 0 as the default packet separation if True
packSep = 0		#change below, in for loop
startSeparation=0
addBias=0
frequency=100		#starting frequency
freqStep=0		#delta frequency







print "*****************************************************************************************"
print "********************************Running with the parameters:*****************************"
print "*****************************************************************************************"
print "***Used modules:", ourModuleIDList
print "***Trigger Module:", triggerModule
print "***Vped:", VpedList
print "***Number of data blocks:", numBlock
if(HV==1):
	print "***High Voltage: ON"
else:
	print "***High Voltage: OFF"
print "***Run duration:", runDuration
print "***Threshold Scan:", threshScan
print "***Trigger delay:", delay
print "*****************************************************************************************"
print "*****************************************************************************************"
print "*****************************************************************************************"



logFile_name = "logFiles/dat_"+dataset+".log"
logf = open(logFile_name, 'w')

logf.write("***Used modules: ")
logf.write("[")
for i in ourModuleIDList:
	logf.write("%d, " % i)
logf.write("]\n")
logf.write("***Trigger Module: %d\n" % triggerModule)
logf.write("***Vped-list: ")
logf.write("[")
for i in VpedList:
	logf.write("%d, " % i)
logf.write("]\n")
logf.write("***Number of data blocks: %d\n" % numBlock)
if(HV==1):
	logf.write("***High Voltage: ON\n")
else:
	logf.write("***High Voltage: OFF\n")
logf.write("***Run duration:  %d\n" % runDuration)
logf.write("***Threshold Scan:  %d\n" % threshScan)
logf.write("***Taking data:  %d\n" % dataTaking)
logf.write("***Trigger delay: %d\n" % delay)



logf.close()




firstRun=0
trigger=9	
trigModule=0

#Find the iterator of this module:
if triggerModule in ourModuleIDList:
	print ourModuleIDList.index(triggerModule)
	trigModule = ourModuleIDList.index(triggerModule)
else:
	print "WARNING: Selected trigger module not in Module list!"







board_ipList=[]
for i in ourModuleIDList:
	board_ipList.append(baseIP[DACQ_dict[i]-1]+moduleIP_dict[i])

print "Board IPs are: ", board_ipList

#board_ipList=["192.168.10.45","192.168.10.114","192.168.10.36","192.168.10.109","192.168.10.157", "192.168.10.131"]
#Begin initialization


pi = piCom.executeConnection()
piCom.powerFEE(pi, "0")
time.sleep(5)
piCom.setTriggerMaskClosed(pi)
time.sleep(0.2)
powerVal = 0x0

slot_dict={118:0x800, 125:0x1000, 126:0x2000, 101:0x4000, 119:0x20000, 108:0x40000, 115:0x40000, 121:0x80000, 116:0x80000, 110:0x100000, 128:0x800000, 123:0x1000000, 124:0x2000000, 112:0x4000000, 100:0x10000000, 111:0x20000000, 114:0x40000000, 107:0x80000000}

failureCounter=0
failure=1
#while(failure==1 and failureCounter<3):
piCom.powerFEE(pi, "0")
time.sleep(2)

for mid in ourModuleIDList:
	powerVal+=slot_dict[mid]
	print(hex(powerVal))
	piCom.powerFEE(pi, str(hex(powerVal)))
	time.sleep(0.8)
	
#	powerVal+=slot_dict[118]
#	print(hex(powerVal))
#	piCom.powerFEE(pi, str(hex(powerVal)))
#	time.sleep(0.8)
	
piCom.setHoldOff(pi,"c350") #c350 for 200 us, ffdc for 262 us (max according to manual)
time.sleep(0.5)
piCom.enableTACK(pi)
time.sleep(20)

failure, moduleList = runInit.Init(my_ip=std_my_ip,board_ipList=board_ipList, ourModuleIDList=ourModuleIDList, pi=pi)
failureCounter+=1

if(failure):
		print "Connection not established!"
		print "Exit data taking!"
#		piCom.powerFEE(pi, "0")
		sys.exit()




	

kBufferDepth = 40000

kNPacketsPerEvent = 64 #64 #One per channel, but for two modules now
channelsPerPacket = 16 #FIXME 8
packetsPerEvent = (kNPacketsPerEvent*len(moduleList) )/channelsPerPacket
kPacketSize = 2*(10 + channelsPerPacket*(numBlock*32 + 1) ) #you can read it on wiresharks, this is the packetsize in bytes. Wireshark will add 44

#Setup the modules:
'''
listener = target_io.DataListener(kBufferDepth, packetsPerEvent, kPacketSize)
buf = listener.GetEventBuffer()

print "Ping data-port"
for module in moduleList:
	module.DataPortPing()
listener.AddDAQListener(std_my_ip[0])
listener.AddDAQListener(std_my_ip[1])
listener.StartListening()
'''

with open(rateTestOut, 'a') as rateTestFile:
	wr = csv.writer(rateTestFile)
	wr.writerow(["run #","freq","delay (us)","events","exp_pack","rec_pack","diff","diff/exp","triggers"])
for j in range(1):
	# [run#,freq,delay(us),events,exp_pack,rec_pack,diff,diff/exp]
	rateList = [0]*9
	rateList[1]=frequency
	try: 
		ld.setLED(frequency,fastLEDFlasherON,fastLEDFlasherON)
		print "The LED frequency is:", frequency, "Hz."
	except:
		print "The LED is not available"
	frequency+=freqStep
	packSep=startSeparation		#change this value for a different starting package separation
	if defaultSep:
		packSep=0
	for i in range(numberOfRuns):
		for i in range(len(moduleList)):
			tuneModule.getTunedWrite(ourModuleIDList[i],moduleList[i],VpedList[i], pi, HV=HV, numBlock=numBlock, addBias=addBias)
		addBias=i*0
		print "package delay in step of 128 ns: ", packSep
		rateList[2]=(packSep*128.)/1000
		for module in moduleList:
			module.WriteRegister(0x71,packSep) #FIXME
			ret, delayRegVal = module.ReadRegister(0x71)
			print hex(delayRegVal)
		if changePackDelay:	
			packSep+=10		#was 80 before
#		buf.Clear()
		print delay
		outRunList, outFileList, nEvents, nPacketsWritten, nTriggers = LEDPulseWFs.LEDPulseWaveforms(moduleList, \
#								listener, \
#								buf, \
								pi, \
								threshScan=threshScan, \
								dataTaking=dataTaking, \
								trigModule=trigModule, \
								triggerModule=triggerModule, \
								frequency=frequency, \
								trigger=trigger, \
								runDuration=runDuration, \
								asicList=asicList, \
								groupList=groupList, \
								numBlock=numBlock, \
								triggerDly=delay, \
								my_ip=std_my_ip, \
								outputDir=outputDir, \
								dataset=dataset, \
								base_thresh=base_thresh, \
								channelsPerPacket=channelsPerPacket)
	#	time.sleep(400)
	#	delay=delay+100    ###648
		rateList[0]=outRunList[0]			#run number
		rateList[3]=nEvents				#num Events
		rateList[8]=nTriggers				#num Triggers
		rateList[4]=nEvents*packetsPerEvent		#expected packets
		rateList[5]=nPacketsWritten			#received packets
		rateList[6]=rateList[4]-rateList[5]		#expected - received = diff
		if(rateList[5]>0):
			rateList[7]=rateList[6]/float(rateList[4])	#diff/exp
		else:
			rateList[7] = 0
		with open(rateTestOut, 'a') as rateTestFile:
			wr = csv.writer(rateTestFile)
			wr.writerow(rateList)
		dataset = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M')
		if changeVped:	
			for g in range(len(VpedList)):
				VpedList[g]=VpedList[g]+VpedChange


#listener.StopListening()


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



runInit.Close(moduleList)

piCom.powerFEE(pi,"0")


runListFile.close()
fileListFile.close()

print "Suite finished"



