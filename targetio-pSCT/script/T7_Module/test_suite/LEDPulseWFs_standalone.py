#!/usr/bin/env python

import run_control
import target_driver
import LED
import target_io
import numpy
from LED import *
import IO
import logRegisters
import logging

kBufferDepth = 50000 #should accomodate up to 50000 events and comply with available memory space for most event sizes
std_my_ip = "192.168.1.2"
std_kNPacketsPerEvent = 64 #One per channel
thresh=[750,900,900,850,700,850,850,700,700,800,800,600,900,900,900,850]

"""
The function runs the system with LED on with external or internal trigger
tester: tester board object
module: module object (FEE)
frequency: freq in Hz of LED flasher
trigger: {0 : 'external', 1 : 'internal', 2 : external without signal (so just noise test)}, 3 : internal trigger without LED (to find dark noise)
runDuration: how long the run is in seconds
"""
def LEDPulseWaveforms(tester,module,frequency,trigger,runDuration, groupList=[1], numBlock=2, deadtime=12500, triggerDly=580, my_ip=std_my_ip, kNPacketsPerEvent=std_kNPacketsPerEvent,thresh=thresh, outputDir="output/"):
	#Set Vped, enable all channels for readout
#	if(trigger==4):
#	module.WriteSetting("EnableChannel0", 0xffffffff)
#	module.WriteSetting("EnableChannel1", 0xffffffff)
#	module.WriteSetting("Zero_Enable", 0x1)
#	kNPacketsPerEvent=4

	if(trigger==4):
		fail = module.WriteSetting("HV_Enable", 0x0)
		logging.info("HV OFF: %d", fail)
#	else:
#		fail = module.WriteSetting("HV_Enable", 0x1)
#		logging.info("HV ON: %d", fail)
#	time.sleep(0.1)


	outRunList=[]
	outFileList=[]


#	ld=LED()
	hostname = run_control.getHostName()
	outdirname = run_control.getDataDirname(hostname)
	runID = run_control.incrementRunNumber(outdirname)
	outdirname = outputDir
	outFile = "%s/run%d.fits" % (outdirname,runID)
	outRunList.append(runID)
	outFileList.append(outFile)
	print "Writing to: %s" % outFile
#	numblock = 2
	#if multiple channels depend on FPGA settings
	kPacketSize = 22 + numBlock*64 #you can read it on wiresharks

	#the listener listens for data coming between the testerboard and computer and writesthe data  to a ringbuffer
	#Set up IO
	buf, writer, listener = IO.setUp(my_ip, kBufferDepth, kNPacketsPerEvent, kPacketSize, outFile)

	#used to switch on the LED
#	if( trigger==0):
#		ld.setLED(frequency,1,1) #run with trigger output enabled.
#	elif( trigger==1):
#		ld.setLED(frequency,0,1) #run only with flash enabled.
#	elif( trigger==2):	
#		ld.setLED(frequency,1,0) #run only with trigger enabled to record noise waveforms.
#	elif( trigger==3):
#		ld.LEDoff() #Turn LED off, run with internal trigger to record noise waveforms.
#	elif( trigger==4):
#		ld.setLED(frequency,1,0) #run only with trigger enabled to record noise waveforms.
#	elif( trigger==9):
#		ld.LEDoff() #Turn LED off, run with internal trigger to record noise waveforms.

	time.sleep(1)

	if( trigger==9):
		print "Start taking software triggers."	
	
		module.WriteSetting("Row",5)
		module.WriteSetting("Column",0)
	
#		tester.EnableSoftwareTrigger(True)
		writer.StartWatchingBuffer(buf)
	
		starttime = time.time()
		for i in range(int(runDuration*frequency) ):
	
#			tester.SendSoftwareTrigger()
			time.sleep(1.0/(2.0*frequency) )
	
		endtime = time.time()
		print "Stop taking data after", endtime-starttime, "seconds."
		writer.StopWatchingBuffer()
#		tester.EnableSoftwareTrigger(False)
	 	logRegisters.logRegister(module, outdirname, runID)


	else:
		if (trigger%2)==0: #for external trigger
			##module.WriteSetting("TriggerDelay",93) #to tell the FPGA how far to look back in time in order to see the actual trigger (acounting for the time it took everything to communicate)
			module.WriteSetting("TriggerDelay",triggerDly) #to tell the FPGA how far to look back in time in order to see the actual trigger (acounting for the time it took everything to communicate)
				
			time.sleep(1)
			module.WriteSetting("TACK_EnableTrigger",0x10000)
			module.WriteSetting("ExtTriggerDirection",1)

			writer.StartWatchingBuffer(buf) #here the ring buffer is observed, but no data is coming in yet
			print "Start taking data for", runDuration, "seconds."
			starttime = time.time()
#			tester.EnableExternalTrigger(True) #data is produced
			time.sleep(runDuration)
#			tester.EnableExternalTrigger(False) #stop producing data
	#		if(trigger==4):
	#			LEDON=0
	#			ld.setLED(frequency,1,0) #run with trigger output enabled.
	#			tester.EnableExternalTrigger(True) #data is produced
	#			for i in range(runDuration):
	#				time.sleep(1)
	#				if(LEDON):
	#					LEDON=1
	#					ld.setLED(frequency,1,1) #run with trigger output enabled.
	#				else:
	#					LEDON=0
	#					ld.setLED(frequency,1,0) #run with trigger output enabled.
	#
	#			tester.EnableExternalTrigger(False) #stop producing data
	
			endtime = time.time()
			print "Stop taking data after", endtime-starttime, "seconds."
			writer.StopWatchingBuffer() #stops looking at the ring buffer
			
	 		logRegisters.logRegister(module, outdirname, runID)
			
	###		outRunList[outRunList.index([runID])].append(["EXT"])
		elif (trigger%2)==1: #for internal trigger
#			tester.SetTriggerModeAndType(0b00, 0b00) #makes sure the internal trigger is used
#			tester.SetTriggerDeadTime(deadtime) #deadtime is the time the trigger is disabled after it has sent out data
			
	
			module.WriteSetting("TriggerDelay",triggerDly) #to tell the FPGA how far to look back in time in order to see the actual trigger (acounting for the time it took everything to communicate)
			for asic in range(4):
				for group in range(4):
					module.WriteASICSetting("Thresh_{}".format(group), asic, int(thresh[asic*4+group]), True) #sets the trigger threshold that has been determined in another test
#					tester.EnableTrigger(asic,group,False)
			#this loop enables the trigger for the groups icluded in grouplist
			starttime = time.time()
			for trgroup in groupList:
				asic=int(trgroup)/4
				group=int(trgroup)%4
				print "Enable trigger for:", asic, group 
#				tester.EnableTrigger(asic,group,True)
			#print "Start taking data for", runDuration, "seconds."
	
	
			writer.StartWatchingBuffer(buf) #starts watching the ring buffer
			time.sleep(runDuration)
			writer.StopWatchingBuffer()
	###		outRunList[outRunList.index([runID])].append(groupList)
			#switch off all trigger again
			for trgroup in groupList:
				asic=int(trgroup)/4
				group=int(trgroup)%4 
#				tester.EnableTrigger(asic,group,False)
			endtime = time.time()
			print "Stop taking data after", endtime-starttime, "seconds."
		
 			logRegisters.logRegister(module, outdirname, runID)
	
		#Turns off LED, but only if on before!
#	if(trigger<3):
#		ld.LEDoff()
#	ld.close()
	IO.stopData(listener, writer)
	
	return outRunList, outFileList
