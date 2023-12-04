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
import subprocess
import tuneModule
import resource
#kBufferDepth = 50000 #should accomodate up to 50000 events and comply with available memory space for most event sizes
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


def activateMAX1230(module, adcList):
	value = np.uint32(0)
	for i in adcList:
		value|=(0x1 << 8+i)
	value|=(0x1 << 31)
	print "Writing value: ", hex(value), "to register."
	module.WriteRegister(0x15, value)

def readTemperature(module):
	adcList=[0,1,2,3]
	value = np.uint32(0)
	activateMAX1230(module, adcList)
	time.sleep(0.1)
	value = module.ReadRegister(0x34)[1]

	temperature=np.zeros(2)
	temperature[0] = np.uint32( (value >> 16) & 0xfff )/8.0
	temperature[1] = np.uint32( (value) & 0xfff )/8.0
	return temperature


def LEDPulseWaveforms(moduleList, pi, threshScan=0, dataTaking=1, trigModule=0, triggerModule=0, frequency=200, trigger=9, runDuration=5, asicList=[0], groupList=[1], numBlock=2, deadtime=12500, triggerDly=580, my_ip=std_my_ip, kNPacketsPerEvent=std_kNPacketsPerEvent,thresh=thresh, outputDir="output/", dataset="testing", base_thresh=500, channelsPerPacket=8, modTrigEn=0, calTrigEn=0, kBufferDepth=20000, local_rsync=True, modFrequency=1000, calFrequency=500,mem_leak_fix = 0):

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
	
	triggerOutdirname = os.environ['HOME']+'/target5and7data/'

        #Check if remote data directory is mounted
        print "Checking if remote output directory is mounted"
        if os.path.ismount(os.environ['HOME']+'/target5and7data')==True:
            print "Output directory is mounted"
            #Check rsync preference and make local output directory if neccessary
            if local_rsync==True:
                print "Writing data with rsync enabled"
                print "Checking if local output directory exists"
##                outdirname = os.environ['HOME']+'/bp_testsuite/trunk/local_outputDir'
                outdirname = '/data/local_outputDir'
                try:
                        os.mkdir(outdirname)
                        print "No local output directory found: making it now..."
                except:
                        print "local output directory found"
            else:
                print "Writing data with rsync disabled"
                outdirname = outputDir
        #Stop if the remote directory isn't mounted
        else:
            print "Cannot connect to the remote output directory!"
            print 'Make sure ',os.environ['HOME']+'/target5and7data',' is mounted!'
            print 'Stopping Data Taking'
            raise SystemExit

	outFile = "%s/run%d.fits" % (outdirname,runID)
        outLogFile = "%s/run%d.log" % (outdirname,runID)
	outRunList.append(runID)
	outFileList.append(outFile)
	print "Writing to: %s" % outFile
	
	print "Setting maximum number of channels per packet to:", channelsPerPacket
	for module in moduleList:
		module.WriteSetting("MaxChannelsInPacket", channelsPerPacket)
	#if multiple channels depend on FPGA settings
	kPacketSize = 2*(10 + channelsPerPacket*(numBlock*32 + 1) ) #you can read it on wiresharks, this is the packetsize in bytes. Wireshark will add 44

	packetsPerEvent = (kNPacketsPerEvent*len(moduleList) )/channelsPerPacket

	refThresh=0
	
	print "Reading module temperature:"
	temp = readTemperature(moduleList[trigModule])	
	print "The temperature of the secondary board is: ", temp[0], "C and", temp[1], "C"
 
	#used to switch on the LED
	count=0
	for module in moduleList:
		count+=1
		module.WriteSetting("TriggerDelay",triggerDly)
		time.sleep(1)
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
	statsVal = np.uint16(statsReg[1] & 0xffff)
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
	holdVal = np.uint16(0)
	statsVal1 = 0
	holdVal1 = np.uint16(0)
	goodThresh=0


	#Read ASIC temperature:
	#moduleList[trigModule].SetADC1230(True, True, True, True, 0x7)




	##moduleList[trigModule].WriteASICSetting("Thresh_{}".format(3), 1, refThresh, True)
	if(threshScan==1):
#			moduleList[trigModule].WriteSetting("EnableTriggerInput", 0xf)
#			moduleList[trigModule].WriteSetting("TriggerEff_Enable", 0xf)
#			moduleList[trigModule].WriteSetting("TriggerEff_Duration", 0xFFFFFF)
		##print "Open trigger mask now!"
		time.sleep(1)
		for asic in asicList:
		   if(asic<99):
		      for gr in groupList:
			print "***********************************************"
			print "*************** Scan asic: ********************"
			print "*******************",asic,"************************"
			effoutbase = triggerOutdirname+'/cameraIntegration/triggerScan/FEE'+str(triggerModule)
			effout = effoutbase+'/dat_'+dataset+'_run'+str(runID)
			print "Writing to directory:", effout
			if not os.path.isdir(effoutbase):
				try:
					os.mkdir(effoutbase)
				except:
					print "Directory", effoutbase, " could not be created!"

			if not os.path.isdir(effout):	
				try:
					os.mkdir(effout)
				except:
					print "Directory", effout, " could not be created (it probably already exists)!"
			
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
			piCom.setTriggerMask(pi)
			#piCom.setTriggerMaskSingle(pi, 23, asic, gr, output=1)
			##moduleList[trigModule].WriteASICSetting("Thresh_{}".format(refGROUP), asic, refThresh, True)
			##moduleList[trigModule].WriteASICSetting("Thresh_{}".format(3), 1, refThresh, True)
			time_frame = 1.0		
			for i in range(0,1600,50):
				moduleList[trigModule].WriteASICSetting("Thresh_{}".format(gr), asic, int(i), True)
				time.sleep(0.2)
				statsReg = moduleList[trigModule].ReadRegister(0xf)
				holdVal = np.uint16(statsReg[1] & 0xffff)
				time.sleep(time_frame)
				statsReg = moduleList[trigModule].ReadRegister(0xf)
				holdVal1 = np.uint16(statsReg[1] & 0xffff)
				if(holdVal1 >= holdVal):
					statsVal = ( holdVal1 - holdVal )/time_frame
				else:
					statsVal = ( holdVal1 + 65535 - holdVal )/time_frame
				
				if(asic==0):
					if(statsVal>0 and goodThresh==0 and i>30):
						if(statsVal>2000):
							goodThresh = i - int(10.0*(statsVal-2000.0)/statsVal)
							print "Found threshold: ", goodThresh
					#		break
				if(i==0): statsVal=0
				
				trigCount1 = piCom.requestTrigCount(pi)
				time.sleep(time_frame)
				trigCount2 = piCom.requestTrigCount(pi)
				trigRate = (trigCount2 - trigCount1)/(1.0*time_frame)
				
				print asic, gr, i, statsVal, trigRate
				outFileThresh.write("%d  %f\n"%(i, trigRate))	#statsVal	
			time.sleep(0.5)
		#	moduleList[trigModule].WriteASICSetting("Thresh_{}".format(refGROUP), asic, 0, True)
			time.sleep(0.1)
			moduleList[trigModule].WriteASICSetting("Thresh_{}".format(gr), asic, 0, True)
			time.sleep(0.5)
			outFileThresh.close()
		   if(asic==99):
			piCom.setTriggerMask(pi)
			print "***********************************************"
			print "*************** Scan asic: ********************"
			print "*******************",asic,"************************"
			effoutbase = triggerOutdirname+'/cameraIntegration/triggerScan/FEE'+str(triggerModule)
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
								holdVal = np.uint16(statsReg[1] & 0xffff)
								time.sleep(time_frame)
								statsReg = moduleList[trigModule].ReadRegister(0xf)
								statsVal = ( np.uint16(statsReg[1] & 0xffff) - holdVal )/time_frame
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
		   if(asic==999):
			piCom.setTriggerMask(pi)
			print "***********************************************"
			print "*************** Scan asic: ********************"
			print "*******************",asic,"************************"
			effoutbase = triggerOutdirname+'/cameraIntegration/triggerScan/FEE'+str(triggerModule)
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
			
			modList = [123, 128]
			asic1=0 
			asic2=0

			for asic0 in range(0,1):
			  for gr0 in range(0,1):
			     for mod1 in range(2):
			      for asic1 in range(4):
				for gr1 in range(4):
				   #for mod2 in range(len(modList)):
				     #for asic2 in range(4):	
					#for gr2 in range(4):
					    #print 'asic0:{}, gr0:{}, mod1:{}, asic1:{}, gr1:{}, mod2:{}, asic2:{}, gr2:{}'.format(asic0, gr0, mod1, asic1, gr1, mod2, asic2, gr2)
					    #outname = '/m{}a{}g{}_m{}a{}g{}_m{}a{}g{}.txt'.format(123, asic0, gr0, modList[mod1], asic1, gr1, modList[mod2], asic2, gr2)
					    outname = '/m{}a{}g{}_m{}a{}g{}.txt'.format(123, asic0, gr0, modList[mod1], asic1, gr1)
					    effoutname = effout+outname
					    outFileThresh = open(effoutname, 'w')
					    time_frame = 2.0		
					    for i in [0,800,1500]:
						moduleList[mod1].WriteASICSetting("Thresh_{}".format(gr1), asic1, int(i), True)
						time.sleep(0.5)
						#moduleList[mod2].WriteASICSetting("Thresh_{}".format(gr2), asic2, int(i), True)
						#time.sleep(0.5)
						moduleList[trigModule].WriteASICSetting("Thresh_{}".format(gr0), asic0, int(i), True)
						time.sleep(0.5)
						statsReg = moduleList[trigModule].ReadRegister(0xf)
						holdVal = np.uint16(statsReg[1] & 0xffff)
						time.sleep(time_frame)
						statsReg = moduleList[trigModule].ReadRegister(0xf)
						statsVal = ( np.uint16(statsReg[1] & 0xffff) - holdVal )/time_frame
						if(gr1==0):
							if(statsVal>0 and goodThresh==0 and i>30):
								if(statsVal>95 and statsVal<110):
									goodThresh = i
									print "Found threshold: ", goodThresh
						if(i==0): 
							statsVal=0
						#print '123', asic0, gr0, modList[mod1], asic1, gr1, modList[mod2], asic2, gr2, i, statsVal
						print '123', asic0, gr0, modList[mod1], asic1, gr1, i, statsVal
						outFileThresh.write("%d  %f\n"%(i, statsVal))
						time.sleep(0.5)
						moduleList[mod1].WriteASICSetting("Thresh_{}".format(gr1), asic1, 0, True)
						time.sleep(0.1)
						#moduleList[mod2].WriteASICSetting("Thresh_{}".format(gr2), asic2, 0, True)
						#time.sleep(0.5)
						moduleList[trigModule].WriteASICSetting("Thresh_{}".format(gr0), asic0, 0, True)
						time.sleep(0.5)
			outFileThresh.close()
		
		   if(asic==9999):
			print "***********************************************"
			print "*************** Scan asic: ********************"
			print "*******************",asic,"************************"
			effoutbase = triggerOutdirname+'cameraIntegration/triggerScan/FEE'+str(triggerModule)
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

			outname = '/PE_scan.txt'
			hitOutname = '/PE_scan_hit_pattern.txt'
			effoutname = effout+outname
			hitEffoutname = effout+hitOutname
			outFileThresh = open(effoutname, 'w')
			outFileHits = open(hitEffoutname, 'w')
			time_frame = 6.0
			OffsetList =np.array([1669, 1664, 1680, 1619, 1648, 1662, 1644, 1645, 1512, 1589, 1539, 1600, 1516, 1562, 1566, 1528])
			SlopeList = np.array([48, 46, 45, 48, 50, 47, 45, 52, 46, 48, 44, 54, 48, 43, 45, 49])		
			#ThreshLevelList_start = np.array([729, 754, 804, 679, 665, 743, 754, 615, 604, 643, 654, 540, 565, 704, 679, 554]) #these trigger levels are for 20PE setting
			for i in range(30,65):
				#ThreshLevelList = OffsetList-SlopeList*i
				ThreshLevelList = np.array( [1600]*16 ) - ( i )*25
				#print ThreshLevelList
				for module in moduleList:
					tuneModule.setTriggerLevel(module, abs(ThreshLevelList) )
				
				statsReg = moduleList[trigModule].ReadRegister(0xf)
				holdVal = np.uint16(statsReg[1] & 0xffff)
				piCom.setTriggerMask(pi)
				startTime=time.time()
				for j in range(50):
					pattern = piCom.requestHitPattern(pi)
					outFileHits.write("%d   " % i)
					for k in pattern:
						outFileHits.write("%s   " % k)
					outFileHits.write("\n")
					piCom.resetHitPattern(pi)
				#time.sleep(10)
				stopTime=time.time()
				piCom.setTriggerMaskClosed(pi)
				time_frame=stopTime-startTime
				
				statsReg = moduleList[trigModule].ReadRegister(0xf)
				holdVal1 = np.uint16(statsReg[1] & 0xffff)
				if(holdVal1 >= holdVal):
					statsVal = ( holdVal1 - holdVal )/time_frame
				else:
					statsVal = ( holdVal1 + 65535 - holdVal )/time_frame
				print  i, time_frame, statsVal, ThreshLevelList
				outFileThresh.write("%d  %f\n"%(i, statsVal))
				time.sleep(0.5)
			outFileHits.close()
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
	if(dataTaking==1):
		statsReg = moduleList[trigModule].ReadRegister(0xf)
		holdVal = np.uint16(statsReg[1] & 0xffff)
		print "The threshold will be set to:", goodThresh
		moduleList[trigModule].WriteASICSetting("Thresh_{}".format(0), 0, goodThresh, True)
		time.sleep(0.1)
		moduleList[trigModule].WriteASICSetting("Thresh_{}".format(1), 0, goodThresh, True)
		time.sleep(0.1)
		moduleList[trigModule].WriteASICSetting("Thresh_{}".format(2), 0, goodThresh, True)
		time.sleep(0.1)
		moduleList[trigModule].WriteASICSetting("Thresh_{}".format(3), 0, goodThresh, True)
		time.sleep(0.1)
		print "Reading", packetsPerEvent, "packets per event."
		statsReg = moduleList[trigModule].ReadRegister(0xf)
		holdVal = np.uint16(statsReg[1] & 0xffff)
		
		writer = target_io.EventFileWriter(outFile, packetsPerEvent, kPacketSize)
		#Moved this up above pinging for testing	
		print "The used ip is: ", my_ip
		print "The used buffer depth:", kBufferDepth
		print "The used packets per event:", packetsPerEvent
		print "The used packetsize:", kPacketSize
		listener = target_io.DataListener(kBufferDepth, packetsPerEvent, kPacketSize)
		
		for server_ip in my_ip:	
			listener.AddDAQListener(server_ip)
		
		print "Ping data-port"
		pingStart=time.time()
		for module in moduleList:
			module.DataPortPingExistingListener()
		pingDone=time.time()
		print "Pinging took", pingDone-pingStart, "seconds."
		
	
	

		listener.StartListening()
		

		#We want to check the temperature every minute. So take the runDuration and divide it into segments:
		tempCheckTime = 60
		tempLeftoverTime = runDuration%tempCheckTime
		tempTimeSteps = runDuration/tempCheckTime


		buf = listener.GetEventBuffer()
		writer.StartWatchingBuffer(buf)
		piCom.setTriggerMask(pi)
		starttime = time.time()
		
		# can check trigger counts while taking data
		
		if(modTrigEn):	
			print "Initializes sending global MODULE trigger" 
			piCom.sendModTrig(pi,runDuration,modFrequency)
			print "Done initialize sending Global trigger"
			time.sleep(1)	
		if(calTrigEn):
			print "Initializes sending global CAL trigger" 
			piCom.sendCalTrig(pi,runDuration,calFrequency)
			print "Done initialize sending Global trigger"
			time.sleep(1)	
		"""	
		#Read temperature frequently!			
		for i in range(tempTimeSteps):
			time.sleep(tempCheckTime)
			print "Reading module temperature:"
			temp = readTemperature(moduleList[trigModule])	
			print "The temperature of the secondary board is: ", temp[0], "C and", temp[1], "C"
			#Prevent the module from overheating:
			#if(temp[0]>40 or temp[1]>40):
			#	piCom.setTriggerMaskClosed(pi)	
			#	return outRunList, outFileList, 0, 0, 0
		
		time.sleep(tempLeftoverTime)
		"""
		time.sleep(runDuration)
		piCom.setTriggerMaskClosed(pi)
		endtime = time.time()
		print "Stop taking data after", endtime-starttime, "seconds."
		time.sleep(0.3)
		print "Stop watching the buffer."
		writer.StopWatchingBuffer()

		statsReg = moduleList[trigModule].ReadRegister(0xf)
		holdVal1 = np.uint16(statsReg[1] & 0xffff)
		if(holdVal1 > holdVal):
			statsVal = ( holdVal1 - holdVal )
		else:
			statsVal = ( holdVal1 + 65535 - holdVal )

		logRegisters.logRegister(moduleList[0], outdirname, runID)
		print "Stop listening."
		#IO.stopData(listener, writer)
		listener.StopListening()
		writer.Close()
		nPacketsWritten = writer.GetPacketsWritten()
		print "thstener.GetEventBuffere number of packets:", nPacketsWritten, "*********************************************************************************************"
		reader = target_io.EventFileReader(outFile)
		nEvents = reader.GetNEvents()
		print "number of events", nEvents, "********************************************************************************************" 
		reader.Close()
		print "number of triggers", statsVal, "***************************************************************************************************"
#			for module in moduleList:
#				module.DeleteDAQListeners()
#				module.CloseSockets()

#			listener.CloseSockets()

		print "Ping data-port"
		pingStart=time.time()
		#for module in moduleList:
		#	message = '1'
		#	resp=''
		# 	resplen = 0;
		#	module.SendAndReceive(message, 1, resp, resplen, 100);

		#	module.DataPortPingExistingListener()
		pingDone=time.time()
		print "Pinging took", pingDone-pingStart, "seconds."


	if(dataTaking==2):
		statsReg = moduleList[trigModule].ReadRegister(0xf)
		holdVal = np.uint16(statsReg[1] & 0xffff)
		print "The threshold will be set to:", goodThresh
		moduleList[trigModule].WriteASICSetting("Thresh_{}".format(0), 0, goodThresh, True)
		time.sleep(0.1)
		moduleList[trigModule].WriteASICSetting("Thresh_{}".format(1), 0, goodThresh, True)
		time.sleep(0.1)
		moduleList[trigModule].WriteASICSetting("Thresh_{}".format(2), 0, goodThresh, True)
		time.sleep(0.1)
		moduleList[trigModule].WriteASICSetting("Thresh_{}".format(3), 0, goodThresh, True)
		time.sleep(0.1)
		print "Reading", packetsPerEvent, "packets per event."
		statsReg = moduleList[trigModule].ReadRegister(0xf)
		holdVal = np.uint16(statsReg[1] & 0xffff)

		effout = triggerOutdirname+'cameraIntegration/RAM_USAGE/'
		#effout = effoutbase+'/dat_'+dataset+'_run'+str(runID)
		print "Writing to directory:", effout

		try:
			os.mkdir(effout)
		except:
			print "Directory", effout, " could not be created!"

		outname = 'Ram_Usage1.txt'
		effoutname = effout+outname
		outFileThresh = open(effoutname, 'a+')
		usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
		outFileThresh.write("%d 0: %f\n" % (runID, usage) )
		

		writer = target_io.EventFileWriter(outFile, packetsPerEvent, kPacketSize)
		print "Ping data-port"
		pingStart=time.time()
		for module in moduleList:
			module.DataPortPing()
		pingDone=time.time()
		print "Pinging took", pingDone-pingStart, "seconds."
		
		print "The used ip is: ", my_ip
		print "The used buffer depth:", kBufferDepth
		print "The used packets per event:", packetsPerEvent
		print "The used packetsize:", kPacketSize
		
						
		listener = target_io.DataListener(kBufferDepth, packetsPerEvent, kPacketSize)
			
		for server_ip in my_ip:	
			listener.AddDAQListener(server_ip)
		usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
		outFileThresh.write("%d 1: %f\n" % (runID, usage) )


		listener.StartListening()
		
		buf = listener.GetEventBuffer()
		writer.StartWatchingBuffer(buf)
		piCom.setTriggerMask(pi)
		starttime = time.time()
		
		# can check trigger counts while taking data
		listener.GetEventBuffer
		if(modTrigEn):	
			print "Initializes sending global MODULE trigger" 
			piCom.sendModTrig(pi,runDuration,modFrequency)
			print "Done initialize sending Global trigger"
			time.sleep(1)	
		if(calTrigEn):
			print "Initializes sending global CAL trigger" 
			piCom.sendCalTrig(pi,runDuration,calFrequency)
			print "Done initialize sending Global trigger"
			time.sleep(1)	
		
		
		
		time.sleep(runDuration)
		
		
		piCom.setTriggerMaskClosed(pi)
		endtime = time.time()
		print "Stop taking data after", endtime-starttime, "seconds."
		time.sleep(0.3)
		print "Stop watching the buffer."
		writer.StopWatchingBuffer()

		statsReg = moduleList[trigModule].ReadRegister(0xf)
		holdVal1 = np.uint16(statsReg[1] & 0xffff)
		if(holdVal1 > holdVal):
			statsVal = ( holdVal1 - holdVal )
		else:
			statsVal = ( holdVal1 + 65535 - holdVal )

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
		for module in moduleList:
			module.DeleteDAQListeners()
			
		
		usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
		outFileThresh.write("%d 2: %f\n" % (runID, usage))
		if(mem_leak_fix):
			listener = None
			writer = None
			reader = None
		usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
		outFileThresh.write("%d 3: %f\n" % (runID, usage) )
		outFileThresh.close()	


        #Perform rsync if required
        if local_rsync==True:
            print "Starting RSYNC: moving run files to "+outputDir
            #cmd = "rsync -tvrq --remove-source-files --omit-dir-times {} {} {}".format(outFile, outLogFile, outputDir)
            cmd = "rsync -tvrq --remove-source-files --omit-dir-times {0}/run{2}.fits {0}/run{2}.log {1}".format(outdirname, outputDir, runID)
            p = subprocess.Popen(cmd, shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
            #p.wait()  #uncomment if you want rsync to finish before next run starts

	return outRunList, outFileList, nEvents, nPacketsWritten, statsVal
