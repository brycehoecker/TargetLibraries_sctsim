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
import logging
import logRegisters

std_eventsPerRun = 1
std_my_ip = "192.168.1.2"
std_tb_ip = "192.168.1.173"
std_board_ip = "192.168.0.173"
std_board_def = "/Users/pkarn/TargetDriver/config/TM7_FPGA_Firmware0xB0000100.def"
std_asic_def = "/Users/pkarn/TargetDriver/config/TM7_ASIC.def"	
std_Vped = 1106

#std_thresh=[400.0, 400.0,400.0, 400.0,400.0, 400.0,400.0, 400.0,400.0, 400.0,400.0, 400.0,400.0, 400.0,400.0, 400.0]
#std_thresh=[300.0, 300.0,300.0, 300.0,300.0, 300.0,300.0, 300.0,300.0, 300.0,300.0, 300.0,300.0, 300.0,300.0, 300.0]
std_thresh=[200.0, 200.0,200.0, 200.0,200.0, 200.0,200.0, 200.0,200.0, 200.0,200.0, 200.0,200.0, 200.0,200.0, 200.0]
#std_thresh=[400.0, 400.0,400.0, 400.0,400.0, 400.0,400.0, 400.0,400.0, 400.0,400.0, 400.0,400.0, 400.0,400.0, 400.0]

def trigCount(tester, timeint, elapsed):
	tester.StartTriggerEfficiencyCounter(timeint)
	while not tester.IsTriggerEfficiencyCounterOutsideDeadTimeCompleted():
		time.sleep(0.05)
	time.sleep(0.2)
	#print "get Efficiency now!"
	count = tester.GetTriggerEfficiencyCounterOutsideDeadTime()
	rate = float(count) / elapsed
	return rate




def setGlobalTrim(module, trimCounts):
	# as long as trimCounts is <= 12 bits, bitwise OR will provide the correct nibbles 
	module.WriteSetting("LowSideVoltage", (0x82000|trimCounts))

def recordModule(module, tester, dataset, testDir, thresh=std_thresh, eventsPerRun=std_eventsPerRun,my_ip=std_my_ip,tb_ip=std_tb_ip,board_ip=std_board_ip,board_def=std_board_def,asic_def=std_asic_def,Vped=std_Vped, outputDir="output/", testASIC=0, testGroup=0, numBlock=2, deadTime=50000):



	outRunList=[]
	outFileList=[]
	module.WriteSetting("Vped_value", Vped)
	trimCounts = 0xc00
	maxTrimCounts = 4096
	minTrimCounts = 0
	stepTrimCounts = 100
	trimCountsList = range(minTrimCounts,maxTrimCounts+1,stepTrimCounts)
	#print trimCountsList
	logging.info(trimCountsList)
	for trimCounts in trimCountsList:
		#print trimCounts
		logging.info(trimCounts)
		saveData = True
		usingFPM = True
	
		# Prepare run number and output file
		hostname = getHostName()
		if saveData:
			outdirname = getDataDirname(hostname)
			runID = run_control.incrementRunNumber(outdirname)
			outdirname = outputDir
			eventfilename = "%s/run%d.fits" % (outdirname,runID)
			logfilename = "%s/breakDown_run%d.log" % (outdirname,runID)
			outFileList.append(logfilename)
			outRunList.append(runID)			
		# If a focal plane module is connected and we want to use it, prepare it
		if usingFPM:
			# measure currents
			#start ADC readout
			module.WriteSetting("MAX11616_Start", 0b1)
			ret, curVal = module.ReadRegister(0x2a)
			ret, volVal = module.ReadRegister(0x2b)
			glbCur = curVal/10.0/2.0
			glbVol = volVal*20.854/1000.0/2.0
#			print "Global current: %f mA." % (glbCur)
#			print "Global voltage: %f V." % (glbVol)
			logging.info("Global current: %f mA.", (glbCur) )
			logging.info("Global voltage: %f V.", (glbVol) )


			# HV
#			print "Turning on HV."
			logging.info("Turning on HV.")
			module.WriteSetting("HV_Enable", 0b1)	#enable distribution from BP
			module.WriteSetting("SelectLowSideVoltage",0b1)	#not sure what this does
			module.WriteSetting("HVDACControl",0b1111)	#selects all ASICs
			module.WriteSetting("LowSideVoltage",0x73000)	#enable HV with 4.096 V reference (most significant 5 nibbles: 29,440 counts)
			module.WriteSetting("LowSideVoltage",0x82800)	# set low side to 2.048 V (x800 DAC counts)
	
			setGlobalTrim(module,trimCounts)
			time.sleep(2)


			module.WriteSetting("EnableChannel0", 0xffffffff)
			module.WriteSetting("EnableChannel1", 0xffffffff)
			module.WriteSetting("Zero_Enable", 0x1)

			module.WriteSetting("NumberOfBuffers", numBlock-1)
			module.WriteSetting("TriggerDelay", 8)

			# internal trigger
			effout1 = testDir + '/breakDownEfficiency_{}/'.format(dataset)
			effout = testDir + '/breakDownEfficiency_{}/{}/'.format(dataset, trimCounts)
			try:
				os.mkdir(effout1)
				os.chmod(effout, 0o777)
			except:
				logging.warning("directory %s already exists", effout1)

			try:
				os.mkdir(effout)
				os.chmod(effout, 0o777)
			except:
				logging.warning("directory %s already exists", effout)

			# list built to check for errors in rates
			trigThreshRate = []	
			
			triggerDly=580
			tester.SetTriggerModeAndType(0b00, 0b00)		

			tester.SetTriggerDeadTime(deadTime)
			module.WriteSetting("TriggerDelay",triggerDly)
			# disabling everything first
			for asic in range(4):
				for group in range(4):
					tester.EnableTriggerCounterContribution(asic, group, False)
					tester.EnableTrigger(asic,group,False)
			# loop to count triggers

			

					outname = 'a{}g{}.txt'.format(asic,group)
					effoutname = effout+outname
					logging.info("saving in %s", effoutname)
					outFile = open(effoutname, 'w')
					outFileList.append(effoutname)
					tester.EnableTriggerCounterContribution(asic,group,True)
		#			tester.EnableTrigger(asic,group,True)
					Thresh_group = "Thresh_{}".format(group)
					module.WriteASICSetting(Thresh_group.format(group), asic, int(thresh[asic*4+group]), True)
					time.sleep(0.2)
					elapsed = 1.0 # run duration in seconds
					duration = elapsed / 8.e-9 # elapsed s / 8 ns => duration time of counting in 8 ns 
					timeint = int(duration)
					eff = trigCount(tester, timeint, elapsed)
					trigThreshRate.append(eff)		
					logging.info("%d   %d   %d   %f", asic, group, int(thresh[asic*4+group]), eff)
					outFile.write("%d %f\n"%(thresh[asic*4+group], eff))
					outFile.close()
		#			tester.EnableTrigger(asic,group,False)
					tester.EnableTriggerCounterContribution(asic, group, False)











#			print "HV is on."
#			print "Starting data taking."
			logging.info("HV is on.")
			logging.info("Starting data taking.")
			currentList = ReadCurrent2(module,printValues=False)
#			print "Currents of all channels (microamps): ", currentList
			logging.info("Currents of all channels (microamps):")
			logging.info(currentList)
			meanCurrent = numpy.mean(currentList)
#			print "Mean current, averaged over all channels, is %f microamps." % meanCurrent
			logging.info("Mean current, averaged over all channels, is %f microamps.", meanCurrent)
			ret, curReg = module.ReadRegister(0x2a)
			ret, volReg = module.ReadRegister(0x2b)
			currentList = numpy.append(currentList,[curReg,volReg])
#			print "Global current: %f mA." % (curReg/10.0/2.0)
#			print "Global voltage: %f V." % (volReg*20.854/1000.0/2.0)
			logging.info("Global current: %f mA.", (curReg/10.0/2.0) )
			logging.info("Global voltage: %f V.", (volReg*20.854/1000.0/2.0) )
			logRegisters.logRegister(module,outdirname,runID)
			if saveData:
				numpy.savetxt(logfilename,currentList,'%f')
#				print logfilename
				logging.info("Writing to file: %s", logfilename)
	
			# Switch off HV
			module.WriteRegister(0x20,0)
			module.WriteSetting("HV_Enable",0)	# disable BP distribution

	return outRunList, outFileList


def getHostName():
        name = socket.gethostname()
#        print "Host name is %s." % name
        logging.info("Host name is %s.", name)
        return name

def getDataDirname(hostname):
        homedir = os.environ['HOME']
        outdirname = '%s/target5and7data/' % homedir

        if os.path.exists(outdirname):
#                print "Ready for writing to %s" % outdirname
                logging.info("Ready for writing to %s", outdirname)
        else:
#                print "ERROR in getDataDirname(): output directory does not exist: %s." % outdirname
                logging.error("ERROR in getDataDirname(): output directory does not exist: %s.", outdirname)
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
#				print "Current of (MAX1230 closely located to) ASIC %d CH %d is %f microamps " % (asic,channel, t)
				logging.info("Current of (MAX1230 closely located to) ASIC %d CH %d is %f microamps ",asic,channel, t)
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
		logging.error("AD conversion is still not valid.")





