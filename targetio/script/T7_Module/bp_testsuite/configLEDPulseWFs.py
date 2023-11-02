#!/usr/bin/env python

import run_control
import target_driver
#import LED
import target_io
import numpy as np
#from LED import *
import IO
import logRegisters
import logging
import time
import piCom
import os

#kBufferDepth = 50000 #should accomodate up to 50000 events and comply with available memory space for most event sizes
kBufferDepth = 20000 #should accomodate up to 50000 events and comply with available memory space for most event sizes
std_my_ip = ["192.168.0.1"]
std_kNPacketsPerEvent = 64 #One per channel, but for two modules now
thresh=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]


"""
The function runs the system with LED on with external or internal trigger
module: module object (FEE)
frequency: freq in Hz of LED flasher
trigger: {0 : 'external', 1 : 'internal', 2 : external without signal (so just noise test)}, 3 : internal trigger without LED (to find dark noise)
runDuration: how long the run is in seconds
"""
def LEDPulseWaveforms(moduleList, pi, threshScan=0, dataTaking=1, trigModule=0, triggerModule=0, frequency=200, trigger=9, runDuration=5, asicList=[0], groupList=[1], numBlock=2, deadtime=12500, triggerDly=580, my_ip=std_my_ip, kNPacketsPerEvent=std_kNPacketsPerEvent,thresh=thresh, outputDir="output/", dataset="testing", base_thresh=500, channelsPerPacket=8):

	nEvents=0
	nPacketsWritten=0
	
	outRunList=[]
	outFileList=[]


#	ld=LED()
	hostname = run_control.getHostName()
	outdirname = run_control.getDataDirname(hostname)
	runID = run_control.incrementRunNumber(outdirname)
	if(dataTaking==0):
		runID=0
	outdirname = outputDir
	outFile = "%s/run%d.fits" % (outdirname,runID)
	outRunList.append(runID)
	outFileList.append(outFile)
	print "Writing to: %s" % outFile
#	numblock = 2
	print "Setting maximum number of channels per packet to:", channelsPerPacket
	for module in moduleList:
		module.WriteSetting("MaxChannelsInPacket", channelsPerPacket)
	#if multiple channels depend on FPGA settings
	kPacketSize = 2*(10 + channelsPerPacket*(numBlock*32 + 1) ) #you can read it on wiresharks, this is the packetsize in bytes. Wireshark will add 44

	packetsPerEvent = (kNPacketsPerEvent*len(moduleList) )/channelsPerPacket
	#the listener listens for data coming between the testerboard and computer and writesthe data  to a ringbuffer
	#Set up IO


	refThresh=0
	

	#used to switch on the LED
	count=0
	if( trigger==9):
		for module in moduleList:
			count+=1
			module.WriteSetting("TriggerDelay",triggerDly)
			time.sleep(1)
			if(count>8):
				module.WriteSetting("DataSendingDelay", 0x280 ) #formerly 0x280
			#elif(count>4):
			#	module.WriteSetting("DataSendingDelay", 0x7D0 ) #formerly 0x280
#			for asic in range(4):
#				for group in range(4):
#					module.WriteASICSetting("Thresh_{}".format(group), asic, int(thresh[asic*4+group]), True) #sets the trigger threshold that has been determined in another test
		print "Start taking data."	
		time.sleep(1)
		

#		module.WriteSetting("TACK_EnableTrigger", 0xFFFF)
#		module.WriteSetting("EnableDeadTimeLogic", 0x1)
#		module.WriteSetting("DurationofDeadtime", 0x60d4)
#		module.WriteSetting("TACK_TriggerDead", 0x40)
#		module.WriteSetting("Row",5)
#		module.WriteSetting("Column",0)
		
		
		inputcount = np.uint32(0)
		effcount = np.uint32(0)
		inputdone = np.uint32(0)
		effdone = np.uint32(0)
#		module.WriteSetting("TriggerEff_Duration",125000000)
#		module.WriteSetting("TriggerEff_Enable",0x8)
#		time.sleep(2)
#		print module.ReadSetting("TriggerInputCounter")
#		time.sleep(1)
#		print module.ReadSetting("TriggerEffCounter")
#		time.sleep(1)
#		inputdone = module.ReadSetting("TriggerInputCounterDone")
#		time.sleep(1)
#		effdone = module.ReadSetting("TriggerEffCounterDone")
		
		statsReg = moduleList[trigModule].ReadRegister(0xf)
		statsReg1 = moduleList[trigModule].ReadRegister(0x5d)
		statsReg2 = moduleList[trigModule].ReadRegister(0x58)
		statsReg3 = moduleList[trigModule].ReadRegister(0x59)
		statsVal = np.uint32(statsReg[1] & 0xffff)
		print("statistics: {}".format(statsVal))
		print("full statistics: {}".format(statsReg))
		
#		inReg = module.ReadRegister(0x58)
#		time.sleep(1)
#		effReg = module.ReadRegister(0x59)
#		time.sleep(1)
#		inputcount = inReg[1] & 0x7fffffff;
#		inputdone = (inReg[1] >> 31) & 0x1;
#		effcount = effReg[1] & 0x7fffffff;
#		effdone = (effReg[1] >> 31) & 0x1;
#		print("Trigger Input Counter: {}").format(inputcount)
#		print("Trigger Eff Counter: {}").format(effcount)
#		print("Trigger Input Counter Done: {}").format(inputdone)
#		print("Trigger Eff Counter Done: {}").format(effdone)
#		print("Input counter register: {}").format(inReg)
#		print("Efficieny counter register: {}").format(effReg)
		
		statsVal = 0
		holdVal = np.uint32(0)
		statsVal1 = 0
		holdVal1 = np.uint32(0)
		goodThresh=0	
		if(threshScan==1):
#			moduleList[trigModule].WriteSetting("EnableTriggerInput", 0xf)
#			moduleList[trigModule].WriteSetting("TriggerEff_Enable", 0xf)
#			moduleList[trigModule].WriteSetting("TriggerEff_Duration", 0xFFFFFF)
			print "Open trigger mask now!"
			piCom.setTriggerMask(pi)
			time.sleep(1)
			for asic in asicList:
			   if(asic<99):
			      for gr in groupList:
				print "***********************************************"
				print "*************** Scan asic: ********************"
				print "*******************",asic,"************************"
				effoutbase = outdirname+'/cameraIntegration/triggerScan/FEE'+str(triggerModule)
				effout = effoutbase+'/dat_'+dataset+'_run'+str(runID)
				print "Writing to directory:", effout
				try:
					os.mkdir(effoutbase)
				except:
					print "Directory", effoutbase, " could not be created!"

				try:
					os.mkdir(effout)
				except:
					print "Directory", effout, " could not be created!"
				
				outname = '/a{}g{}.txt'.format(asic, gr)
				effoutname = effout+outname
				outFileThresh = open(effoutname, 'w')
				refASIC=0
				refGROUP=1
				if(asic==0):
					refThresh=650
					refASIC=1
				elif(asic==1):
					refThresh=600
					refASIC=0
				elif(asic==2):
					refThresh=400
					refASIC=1
				elif(asic==3):
					refThresh=400
					refASIC=2
				if(gr==0):
					refGROUP=1
				elif(gr==1):
					refGROUP=0
				elif(gr==2):
					refGROUP=1
				elif(gr==3):
					refGROUP=2
				refThresh=0
				moduleList[trigModule].WriteASICSetting("Thresh_{}".format(refGROUP), asic, refThresh, True)
				time_frame = 2.0		
				for i in range(0,3000,50):
				#	moduleList[trigModule].WriteSetting("TriggerCounterReset", 0x1)
				#	moduleList[trigModule].WriteSetting("TriggerCounterReset", 0x0)
				#	moduleList[trigModule].WriteRegister(0x58, 0x0)
				#	moduleList[trigModule].WriteRegister(0x59, 0x0)
				#	moduleList[trigModule].WriteSetting("TriggerEff_Duration", 0xFFFFFF)
					moduleList[trigModule].WriteASICSetting("Thresh_{}".format(gr), asic, int(i), True)
					#time.sleep(0.1)
					#moduleList[trigModule].WriteASICSetting("Thresh_{}".format(1), gr, int(i), True)
					time.sleep(0.5)
					statsReg = moduleList[trigModule].ReadRegister(0xf)
					holdVal = np.uint32(statsReg[1] & 0xffff)
				#	statsReg1 = moduleList[trigModule].ReadRegister(0x5d)
				#	holdVal1 = np.uint32((statsReg1[1] >> 16 ) & 0xffff)
					time.sleep(time_frame)
					statsReg = moduleList[trigModule].ReadRegister(0xf)
					statsVal = ( np.uint32(statsReg[1] & 0xffff) - holdVal )/time_frame
				#	statsReg1 = moduleList[trigModule].ReadRegister(0x5d)
				#	statsVal1 = ( np.uint32( (statsReg1[1] >> 16) & 0xffff) - holdVal1)/time_frame
				#	statsReg2 = moduleList[trigModule].ReadRegister(0x58)
				#	statsReg3 = moduleList[trigModule].ReadRegister(0x59)
				#	statsReg4 = moduleList[trigModule].ReadRegister(0x57)
					if(asic==0):
						if(statsVal>0 and goodThresh==0 and i>30):
							if(statsVal>20 and statsVal<430):
								goodThresh = i
								print "Found threshold: ", goodThresh
						#		break
					if(i==0): statsVal=0
					print asic, gr, i, statsVal
					outFileThresh.write("%d  %f\n"%(i, statsVal))
				time.sleep(0.5)
				moduleList[trigModule].WriteASICSetting("Thresh_{}".format(refGROUP), asic, 0, True)
				time.sleep(0.1)
				moduleList[trigModule].WriteASICSetting("Thresh_{}".format(gr), asic, 0, True)
				time.sleep(0.5)
				outFileThresh.close()
			   if(asic==99):
				print "***********************************************"
				print "*************** Scan asic: ********************"
				print "*******************",asic,"************************"
				effoutbase = outdirname+'/cameraIntegration/triggerScan/FEE'+str(triggerModule)
				effout = effoutbase+'/dat_'+dataset+'_run'+str(runID)
				print "Writing to directory:", effout
				try:
					os.mkdir(effoutbase)
				except:
					print "Directory", effoutbase, " could not be created!"

				try:
					os.mkdir(effout)
				except:
					print "Directory", effout, " could not be created!"
				for asic1 in range(4):
					for gr1 in range(4):
						for asic2 in range(4):
							for gr2 in range(4):

								outname = '/a{}g{}_a{}g{}.txt'.format(asic1, gr1, asic2, gr2)
								effoutname = effout+outname
								outFileThresh = open(effoutname, 'w')
								time_frame = 2.0		
								for i in range(800,1500,400):
									moduleList[trigModule].WriteASICSetting("Thresh_{}".format(gr1), asic1, int(i), True)
									time.sleep(0.1)
									moduleList[trigModule].WriteASICSetting("Thresh_{}".format(gr2), asic2, int(i), True)
									time.sleep(0.5)
									statsReg = moduleList[trigModule].ReadRegister(0xf)
									holdVal = np.uint32(statsReg[1] & 0xffff)
									time.sleep(time_frame)
									statsReg = moduleList[trigModule].ReadRegister(0xf)
									statsVal = ( np.uint32(statsReg[1] & 0xffff) - holdVal )/time_frame
									if(gr1==0):
										if(statsVal>0 and goodThresh==0 and i>30):
											if(statsVal>95 and statsVal<110):
												goodThresh = i
												print "Found threshold: ", goodThresh
									if(i==0): statsVal=0
									print asic, i, statsVal
									outFileThresh.write("%d  %f\n"%(i, statsVal))
								time.sleep(0.5)
								moduleList[trigModule].WriteASICSetting("Thresh_{}".format(gr1), asic1, 0, True)
								time.sleep(0.1)
								moduleList[trigModule].WriteASICSetting("Thresh_{}".format(gr2), asic2, 0, True)
								time.sleep(0.5)
								outFileThresh.close()
			

			print "Close trigger mask!"
			piCom.setTriggerMaskClosed(pi)




		print "Wait here"
		time.sleep(0.3)
		print "The selected threshold is: ", goodThresh # "but run at: ",650
		if(goodThresh==0):
			goodThresh = base_thresh
		print "The selected threshold is: ", goodThresh # "but run at: ",650


		refThresh=0	
		time.sleep(2)
		if(dataTaking):
			moduleList[trigModule].WriteASICSetting("Thresh_{}".format(0), 0, refThresh, True)
			time.sleep(0.1)
			moduleList[trigModule].WriteASICSetting("Thresh_{}".format(1), 0, goodThresh, True)
			time.sleep(0.1)
			print "Reading", packetsPerEvent, "packets per event."
			statsReg = moduleList[trigModule].ReadRegister(0xf)
			holdVal = np.uint32(statsReg[1] & 0xffff)
			
			print "Ping data-port"
			for module in moduleList:
				module.DataPortPing()
			
			print "The used ip is: ", my_ip
			print "The used buffer depth:", kBufferDepth
			print "The used packets per event:", packetsPerEvent
			print "The used packetsize:", kPacketSize
			
			listener = target_io.DataListener(kBufferDepth, packetsPerEvent, kPacketSize)
				
				
			listener.AddDAQListener(my_ip[0])
			listener.AddDAQListener(my_ip[1])
			

			listener.StartListening()
			
			writer = target_io.EventFileWriter(outFile, packetsPerEvent, kPacketSize)
			buf = listener.GetEventBuffer()
			

			writer.StartWatchingBuffer(buf)
			piCom.setTriggerMask(pi)
			starttime = time.time()
			
			# can check trigger counts while taking data
			
			
			print "Initializes sending global trigger" 
#			piCom.sendCalTrig(pi)
			piCom.sendModTrig(pi)
			print "Done initialize sending Global trigger"
			time.sleep(1)	
			
			
			
			time.sleep(runDuration)
			
			
			piCom.setTriggerMaskClosed(pi)
			endtime = time.time()
			print "Stop taking data after", endtime-starttime, "seconds."
			time.sleep(0.3)
			print "Stop watching the buffer."
			writer.StopWatchingBuffer()

			logRegisters.logRegister(moduleList[0], outdirname, runID)
			print "Stop listening."
			#IO.stopData(listener, writer)
			listener.StopListening()
			writer.Close()
			nPacketsWritten = writer.GetPacketsWritten()
			print "the number of packets:", nPacketsWritten, "*********************************************************************************************"
			reader = target_io.EventFileReader(outFile)
			nEvents = reader.GetNEvents()
			print "number of events", nEvents, "********************************************************************************************" 
			reader.Close()
			print "number of triggers", statsVal, "***************************************************************************************************"
			statsReg = moduleList[trigModule].ReadRegister(0xf)
			statsVal = ( np.uint32(statsReg[1] & 0xffff) - holdVal )
	

	return outRunList, outFileList, nEvents, nPacketsWritten, statsVal
