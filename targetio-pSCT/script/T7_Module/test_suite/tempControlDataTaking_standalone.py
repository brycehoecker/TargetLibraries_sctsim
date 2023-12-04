#!/usr/bin/env python

import runInit_standalone
import target_io
import target_driver
import time
import datetime
import os, sys
import logging
from Peltier_uC import Monitor_uC_POST
import subprocess

from subprocess import Popen, PIPE
from Peltier_uC.FPGAcmd import FPGAcmd
from Peltier_uC.AVRcmd import AVRcmd


HOST =  "192.168.0.173"
HOST0 = "0.0.0.0"
PORT0 = 8106
PORT = 8105

ctlReg = 0x2f # 0x2f for Eval Board
ctlMode = 0x01

delayTime = 0.1

def executeCmd(command):

        output=subprocess.check_output(command+"; exit 0",stderr=subprocess.STDOUT,shell=True, universal_newlines=True)
	print output
        return output

argList = sys.argv

print argList

name = None
purpose = "General test."
logLevel = None
emailAddress = None


##outputDir = "/Users/tmeures/test_suite/output_photon/"
outputDir = "/home/ctauser/target5and7data/"
#outputDir = "output/"
print "Checking if output directory exists and is mounted"
try:
	os.mkdir (outputDir)
except:
	print "Output-directory already exists."

#Check if remote data directory is mounted
if os.path.ismount(os.environ['HOME']+'/target5and7data')==True:
    print "Output-directory is mounted"
else:
    print "Cannot connect to the remote output directory!"
    print 'Make sure ',os.environ['HOME']+'/target5and7data',' is mounted!'
    print 'EXITING'
    raise SystemExit


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


#Initialize looging and produce neede file outputs.
###dataset, testDir, assocRun, assocFile, moduleID, FPM, purpose, user, logFileName, testDirFinal, fitsDir = prepareLog.prepareLog(moduleID, FPM, name, purpose, logLevel, logToFile, outputDir)
##dataset = "20160713_0736"

#original_stdout =  sys.stdout
#sys.stdout = logFile 


timestamp = time.time()
dataset = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M')
assocRun = "runList.txt"
assocFile = "fileList.txt"

runListFile = open(assocRun,'w')
fileListFile = open(assocFile,'w')

baseIP=["192.168.10.", "192.168.12."]
moduleIP_dict={100:"81",101:"89", 107:"64", 108:"180", 110:"101", 111:"127", 112:"36", 113:"21", 114:"157", 115:"247", 116:"247", 118:"45", 119:"130", 121:"229", 123:"109", 124:"114", 125:"122", 126:"188", 128:"131"}
std_my_ip=["192.168.10.1", "192.168.12.1"]
##DACQ_dict={100:1, 101:2, 107:1, 108:1, 110:2, 111:1, 112:1, 113:1, 114:1, 115:1, 116:1, 118:1, 119:1, 121:1, 123:1, 124:1, 125:2, 126:2, 128:1}
DACQ_dict={100:1, 101:2, 107:2, 108:2, 110:2, 111:2, 112:1, 113:1, 114:1, 115:2, 116:2, 118:2, 119:2, 121:2, 123:1, 124:1, 125:2, 126:2, 128:1}
#moduleIDList=[0,i1,2,3]


#The module distribution inside the camera:
#********** 118  125  126  101 *************
#********** 119  108  121  110 *************
#********** 128  123  124  112 *************
#********** 100  111  114  107 *************



#Which modules we want to run:


ourModuleIDList=[101] #[118, 119, 108, 121, 128, 123, 124, 112, 100, 111, 114, 107]  ##[118, 125, 126, 101, 119, 108, 121, 110, 128, 123, 124, 112, 100, 111, 114, 107]  #[119, 108, 116, 128, 123, 124, 112, 111, 114, 107] 
moduleIDList=range(len(ourModuleIDList))
#What Vped to use:
VpedList = [1106]*len(ourModuleIDList)


#Set these parameters:
triggerModule=101
runDuration= 50 #in seconds
numberOfRuns = 1 #27
HV=0   #(1=ON, 0=OFF)
numBlock=10

#For threshold scan:
threshScan=0 #(1=YES, 0=NO)
asicList=[0,1,2,3]
groupList=[0,1,2,3]

#For datataking:
dataTaking=1
base_thresh=500
changeThresh=0
kBufferDepth = 40000
channelsPerPacket = 1 #FIXME 8
#Do we want to use one of the backplane triggers:
modTrigEn=0
calTrigEn=1
#The trigger delay:
delay=760    ###648 #666 #685

#LED flahser:
fastLEDFlasherON=0
frequency=1000		#starting frequency
freqStep=250		#delta frequency
freqRuns=1
#Special functions:
changeVped=0
VpedChange=5

changeWbias=0
wbias=985

#Run data taking/threshScan, etc...
changePackDelay=0
startSeparation=800
addBias=600


#To check the write parameter structure
changeWriteParams=0
WR_ADDR_Incr1_LE= 3 #63
WR_ADDR_Incr1_TE= 18 #14
WR_STRB1_LE = 32 #35
WR_STRB1_TE = 42 #45
WR_ADDR_Incr2_LE = 35 #37
WR_ADDR_Incr2_TE = 50 #52
WR_STRB2_LE = 0 #2
WR_STRB2_TE = 10 #12
SSPin_LE = 46 #46
SSPin_TE = 61 #61



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
logf.write("***Number of runs:  %d\n" % numberOfRuns)
logf.write("***Threshold Scan:  %d\n" % threshScan)
logf.write("***Taking data:  %d\n" % dataTaking)
logf.write("***Trigger delay: %d\n" % delay)
logf.write("***Base threshold: %d\n" % base_thresh)
logf.write("***Added to nominal bias voltage: %d\n" % addBias)

logf.write("***Change WBias: %d\n" % changeWbias)
logf.write("***Start wbias: %d\n" % wbias)


logf.close()


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

#############################
### TEMP MONITORING BELOW ###
#############################

module,tester = runInit_standalone.Init()
module.WriteSetting("2.7V_Enable", 1)

#outp=executeCmd("./Peltier_uC/cta-avrprog.py --target_host 192.168.0.173 -p m328 -U flash:w:Peltier_uC/hex/PeltierPOST_v6.hex")
##print outp


''' Run Monitor_uC_POST.py until CTRL + C is entered '''


p = Popen("python Peltier_uC/AVRcmd.py -s", stdout=PIPE, shell=True)
''' get child process output '''
'''
print p.stdout.readline()
for i in range(10):
print p.stdout.readline(), # read output
p.communicate(input='\n') # allow parent process to enter input
'''
time.sleep(1)

p = Popen("python Peltier_uC/AVRcmd.py --end_pgm_mode", stdout=PIPE, shell=True)
''' get child process output '''
'''
print p.stdout.readline()
for i in range(10):
print p.stdout.readline(), # read output
p.communicate(input='\n') # allow parent process to enter input
'''
time.sleep(1)

#ctl = FPGAcmd(HOST, PORT, HOST0, PORT0, 1, 102400)
avr = AVRcmd(HOST, PORT, HOST0, PORT0)
ctl = avr.getFPGA()

print '\nTemperature controller serial console'
print 'Press CTRL + C to exit\n'

'''
print 'Test: uC Power On Self Test'
print 'Purpose: Read out uC Self Test information to verify basic hardware connections.'
print 'uC Firmware: PeltierPOST_v5.hex'
print ''
'''

speed = 0x20  # This has a low probability of transfer error by experiment
time.sleep(1)

# set up the uC
ctl.sendCmd(ctlReg, 1, 0x2000, 0)
time.sleep(delayTime)

# Set up the uC SPI speed
ctl.sendCmd(ctlReg, 1, (speed << 8 | ctlMode), 0)
time.sleep(delayTime)

thisLine = ""
errCount = 0 # This counts non-printable chars that are not 6 (ACK)

while True:
	try:
		results = [0,0,0,0] #,0,0,0,0,0,0,0,0]
		# Reset uC buffer pointer
		avr.cmd(0xff)
		# Get 1st block of data (0x16 is SYN Idle)
		data = avr.cmd(0x0)
		results[0] = (data & 0xFF000000) >> 24
		results[1] = (data & 0x00FF0000) >> 16
		results[2] = (data & 0x0000FF00) >> 8
		results[3] = data & 0xFF

		byte = results[0]

		if byte >= 32 and byte <= 126:
			thisLine = thisLine + chr(byte)
		elif byte == 0xd:
			print "AVR:", thisLine
			if "Complete" in thisLine:
				break
			thisLine = ""
		####print hex(results[0]),  hex(results[1]), hex(results[2]), hex(results[3]) 
	
	except KeyboardInterrupt:
		print thisLine
		print "\n\n***"
		print "*** Shutting off FPGA Serial Console"
		print "***\n"
		break
		##time.sleep(1)

runInit_standalone.Close(module, tester)

runListFile.close()
fileListFile.close()

print "Suite finished"



