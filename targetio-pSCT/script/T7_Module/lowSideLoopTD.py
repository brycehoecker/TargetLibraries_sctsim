#!/usr/bin/env python

# Colin Adams
# Created May 18 2016
# TargetDriver version of libTARGET lowSideLoop.py
# (made by Justin Vandenbroucke)
# Loop over low side voltage (in dac counts)
# For each take a run.

import os,sys,socket
import numpy
import time
import run_control
import target_driver

def setTrimVoltage(module, trimCounts):
	# as long as trimCounts is <= 12 bits, bitwise OR will provide the correct nibbles 
	module.WriteSetting("LowSideVoltage", (0x82000|trimCounts))

def recordModule(module,eventsPerRun,trimCounts):
	saveData = True
	usingFPM = True
	
	# Prepare run number and output file
	hostname = getHostName()
	if saveData:
		outdirname = getDataDirname(hostname)
		runID = run_control.incrementRunNumber(outdirname)
		eventfilename = "%s/run%d.fits" % (outdirname,runID)
		logfilename = "%s/run%d.log" % (outdirname,runID)
			
	# If a focal plane module is connected and we want to use it, prepare it
	if usingFPM:
		# measure currents
		#start ADC readout
		module.WriteSetting("MAX11616_Start", 0b1)
		ret, curVal = module.ReadRegister(0x2a)
		ret, volVal = module.ReadRegister(0x2b)
		glbCur = curVal/10.0/2.0
		glbVol = volVal*20.854/1000.0/2.0
		print "Global current: %f mA." % (glbCur)
		print "Global voltage: %f V." % (glbVol)
		# HV
		print "Turning on HV."
		module.WriteSetting("HV_Enable", 0b1)	#enable distribution from BP
		module.WriteSetting("SelectLowSideVoltage",0b1)	#not sure what this does
		module.WriteSetting("HVDACControl",0b1111)	#selects all ASICs
		module.WriteSetting("LowSideVoltage",0x73000)	#enable HV with 4.096 V reference (most significant 5 nibbles: 29,440 counts)
		module.WriteSetting("LowSideVoltage",0x82800)	# set low side to 2.048 V (x800 DAC counts)

		setTrimVoltage(module,trimCounts)
		time.sleep(2)
		print "HV is on."
		print "Starting data taking."
		currentList = ReadCurrent2(module,printValues=False)	#what is the TD equiv?
		print "Currents of all channels (microamps): ", currentList
		meanCurrent = numpy.mean(currentList)
		print "Mean current, averaged over all channels, is %f microamps." % meanCurrent
		ret, curReg = module.ReadRegister(0x2a)
		ret, volReg = module.ReadRegister(0x2b)
		currentList = numpy.append(currentList,[curReg,volReg])
		print "Global current: %f mA." % (curReg/10.0/2.0)
		print "Global voltage: %f V." % (volReg*20.854/1000.0/2.0)
		if saveData:
			numpy.savetxt(logfilename,currentList,'%f')
			print logfilename

		# Switch off HV
		module.WriteRegister(0x20,0)
		module.WriteSetting("HV_Enable",0)	# disable BP distribution
def getHostName():
        name = socket.gethostname()
        print "Host name is %s." % name
        return name

def getDataDirname(hostname):
        homedir = os.environ['HOME']
        outdirname = '%s/target5and7data/' % homedir

        if os.path.exists(outdirname):
                print "Ready for writing to %s" % outdirname
        else:
                print "ERROR in getDataDirname(): output directory does not exist: %s." % outdirname
                sys.exit(1)
        return outdirname

def ReadCurrent2(module,printValues=True):
#	module.SetADC1230(True, True, True, True, 0x7) # configure
	module.WriteSetting("ADC0ChannelSelect", 0b1111) # read all 16 ch
	module.WriteSetting("ADCEnableSelect", 0b1111) # Enable ADC for all 4 ASICs
#	module.StartADC1230() # start AD conversions

	# next 2 lines are TargetDriver analog to StartADC1230()
	module.WriteSetting("ADCStop", 0) # stop AD conversions
	# non sticky bit (only stays up one clock cycle), throws an error, but that is expected
	module.WriteSetting("ADCStart", 1) # start AD conversions
	
	currentList = []
	for asic in range(4):
		for channel in range(16):
			try:
				t = myReadCurrent(asic,channel,module)
				#t = module.ReadCurrent() #target function
			except: # AD conversion is not done?
				time.sleep(0.01) # try sleeping 10 (ms)
				t = myReadCurrent(asic,channel,module) # check the value again
			if printValues:
				print "Current of (MAX1230 closely located to) ASIC %d CH %d is %f microamps " % (asic,channel, t)
			currentList = numpy.append(currentList,t)
	return currentList

def myReadCurrent(asic,channel,module):
	ret, value = module.ReadRegister(0x35 + ((asic)%2)*17 + channel)
	status = value >> (15 if asic/2 == 0 else 31)
	#print "ASIC is ",asic," CH is ",channel
	#print "Reading from Register ",hex(0x35 + ((asic)%2)*17 + channel)
	#print "value is ",hex(value)
	if(status):
		#return (((value >> (0 if asic/2 == 0 else 16)) & 0xFFF)/2.,value) # in (uA)
		return ((value >> (0 if asic < 2 else 16)) & 0xFFF)/2. # in (uA)
	else:
		"AD conversion is still not valid."



if __name__=="__main__":
	eventsPerRun = 1
	my_ip = "192.168.1.2"
	tb_ip = "192.168.1.173"
	board_ip = "192.168.0.173"
	board_def = "/Users/pkarn/TargetDriver/config/TM7_FPGA_Firmware0xB0000100.def"
	asic_def = "/Users/pkarn/TargetDriver/config/TM7_ASIC.def"
	#hostname = run_control.getHostName()
	#outdirname = run_control.getDataDirname(hostname)
	#runID = run_control.incrementRunNumber(outdirname)
	#outFile = "%srun%d.fits" % (outdirname,runID)
	#print "Writing to: %s" % outFile
	module = target_driver.TargetModule(board_def, asic_def, 1)
	InitFail = module.EstablishSlowControlLink(my_ip, board_ip)
	print(InitFail)
	
	print module.Initialise()

	time.sleep(0.1)
        tester = target_driver.TesterBoard()
        tester.Init(my_ip, tb_ip)
        time.sleep(0.1)
        tester.EnableReset(True)
        time.sleep(0.1)
        tester.EnableReset(False)
        time.sleep(0.1)

	VPED = 2500
	module.WriteSetting("Vped_value", VPED)
#	trimCounts = 0xc00

	maxTrimCounts = 4096
	minTrimCounts = 0
	stepTrimCounts = 40

	trimCountsList = range(minTrimCounts,maxTrimCounts+1,stepTrimCounts)
	print trimCountsList
	for trimCounts in trimCountsList:
		print trimCounts
		recordModule(module,eventsPerRun,trimCounts)
	module.CloseSockets()


