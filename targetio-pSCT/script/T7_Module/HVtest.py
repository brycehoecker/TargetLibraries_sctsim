import target_driver
import time
import target_io
import run_control
import BrickPowerSupply
import numpy
#import argparse
import random
from LED import *
import tuneModule
import datetime, shutil, glob
ld=LED()

# Configuration
InitMode = 1 # it will initialize if set to 1, and will jump to data taking if set to 0
PCMode = 2    # 1=try to turn output on first, only used for long duration runs; 2=Power Cycle if fail,turn power supply on before running; 3=Only try to init once
Trigger = 0   # Ext=1 Soft=0 Int=2
TrackDataTakingTime = 0 # if set to 1 it will track data taking time and gives an output in the end
HVMode = 0 # 0: not using HV; 1: old way to set low side; 2: new way to set low side
numBlock = 2
moduleID = 111
Triggerdelay = 93
makelog = 1

# VpedList,multiple Vped values will loop inside power cycle
minVped = 125
maxVped = 4061+1
stepVped = 164
VpedList = range(minVped,maxVped,stepVped)  # the VpedLoop for calibration
#VpedList = [1000]
#VpedList = [1106]*2
#VpedList = range(1000,2001,500)

# FreqList, loop inside power cycle, and inside Vped loop, only works with software or external trigger
#FreqList = range(30,105,5)
FreqList = [500]

# runDurationList, loop inside power cycle, inside Freq loop
runDurationList = [1]

# UnusedVariableList, loop outside power cycle
UnusedVariableList = [1]

# Pixel stuff
singlePixel = 0 # 1=only leave one pixel open
openASIC = 0
openPxl = 0

# sleep time configuration
sleeptime = 10  #sleep time after each run (without PC)
sleepBeforeRun = 1 # sleep time before data taking
sleepPCMode = 1 # sleep time before PC, 1: sleep random integer values from 20s to 30s; 0: fixed sleeptime 
sleepPCtime = 1800 # sleep time before PC when sleepPCMode is set to 0

##ii = 1

my_ip = "192.168.1.2"
tb_ip = "192.168.1.173"
board_ip = "192.168.0.173"
board_def = "/Users/pkarn/TargetDriver/config/TM7_FPGA_Firmware0xB0000100.def"
asic_def = "/Users/pkarn/TargetDriver/config/TM7_ASIC.def"

if TrackDataTakingTime:
	starttimesave = []
	endtimesave = []

for UnusedVariable in UnusedVariableList:
	if InitMode:
		if PCMode == 1:
			InitFail = 1
			while InitFail != 0:
				bps = BrickPowerSupply.BrickPowerSupply('2200','/dev/tty.usbserial')
				time.sleep(0.5)
				bps.open()
				bps.outputOn()
				#bps.setVoltage(12)
				#bps.setMaxCurrent(2.2)
				time.sleep(20)
        			board = target_driver.TargetModule(board_def, asic_def, 1)
        			InitFail = board.EstablishSlowControlLink(my_ip, board_ip)
				print(InitFail)
				if InitFail:
					bps.outputOff()
					time.sleep(15)
		elif PCMode == 2:
			InitFail = 1
        	        while InitFail != 0:
        	                bps = BrickPowerSupply.BrickPowerSupply('2200','/dev/tty.usbserial')
        	                time.sleep(0.5)
        	                bps.open()
        	                board = target_driver.TargetModule(board_def, asic_def, 1)
        	                InitFail = board.EstablishSlowControlLink(my_ip, board_ip)
        	                print(InitFail)
        	                if InitFail:
        	                        bps.outputOff()
        	                        time.sleep(15)
					bps.outputOn()
					time.sleep(30)
		else:
			board = target_driver.TargetModule(board_def, asic_def, 1)
			print board.EstablishSlowControlLink(my_ip, board_ip)

		time.sleep(0.1)
		print board.Initialise()
		time.sleep(0.1)
		tester = target_driver.TesterBoard()
		tester.Init(my_ip, tb_ip)
		time.sleep(0.1)
		tester.EnableReset(True)
		time.sleep(0.1)
		tester.EnableReset(False)
		time.sleep(0.5)
	for Vped in VpedList:
		for Freq in FreqList:
			for runDuration in runDurationList:

	        		hostname = run_control.getHostName()
	        		outdirname = run_control.getDataDirname(hostname)
	        		runID = run_control.incrementRunNumber(outdirname)
	        		outFile = "%srun%d.fits" % (outdirname,runID)
	        		print "Writing to: %s" % outFile

				if InitMode == 0:
					board = target_driver.TargetModule(board_def, asic_def, 1)
					tester = target_driver.TesterBoard()
					print board.EstablishSlowControlLink(my_ip, board_ip)

				#Set Vped, enable all channels for readout
				board.WriteSetting("Vped_value", Vped)
				board.WriteSetting("EnableChannelsASIC0", 0xffff)
				board.WriteSetting("EnableChannelsASIC1", 0xffff)
				board.WriteSetting("EnableChannelsASIC2", 0xffff)
				board.WriteSetting("EnableChannelsASIC3", 0xffff)
				board.WriteSetting("Zero_Enable", 0x1)	
				board.WriteSetting("NumberOfBlocks", numBlock-1)
				board.WriteSetting("TriggerDelay", Triggerdelay)

				if HVMode == 1:

					#HV Control
					#Start MAX11616, HV monitoring
					#print board.WriteRegister(0x1F, 0x80000000)
					#print board.WriteSetting("HV_Enable", 0x0)
					#time.sleep(0.1)
					print board.WriteSetting("HV_Enable", 0x1)
					time.sleep(0.1)
					#Set reference voltage to 4.096V, need to do twice?
					board.WriteRegister(0x20, 0x7300080F)
					board.WriteRegister(0x20, 0x7300080F)
					time.sleep(1)
					#Set low side voltage for all trigger channels to 2.048V
					board.WriteRegister(0x20, 0x8280080F)
				elif HVMode == 2:

		                        print board.WriteSetting("HV_Enable", 0x1)
		                        time.sleep(0.1)
                        		board.WriteSetting("HV_Enable", 0b1)   #enable distribution from BP
                       			board.WriteSetting("SelectLowSideVoltage",0b1) #not sure what this does
                        		board.WriteSetting("HVDACControl",0b1111)      #selects all ASICs
                        		board.WriteSetting("LowSideVoltage",0x73000)   #enable HV with 4.096 V reference (most significant 5 nibbles: 29,440 counts)

				if singlePixel:
					nasics = 4
                                	npxls = 4
                                	asicDict = {0 : 0b0001, 1 : 0b0010, 2 : 0b0100, 3 : 0b1000}
                                	codeload = 0x30000      # 0011 is coden_loadn and allows the writing of a trim voltage to a single trigger pixel
					print "********************** Enabling pixel:", openASIC, openPxl, "*****************************"
	                                for asic in range(nasics):
	                                        board.WriteSetting("HVDACControl", asicDict[asic])
	                                        for pxl in range(npxls):
	                                                trigPxl = int("0x{}000".format(pxl),16)
	                                                if( (asic == openASIC) and (pxl == openPxl) ):
	                                                        trimVoltage = 0xFFF
	                                                else:
	                                                        trimVoltage =0x400
	                                                        #print (codeload|trigPxl|trimVoltage)
	                                                board.WriteSetting("LowSideVoltage", (codeload | trigPxl | trimVoltage))
					time.sleep(1)
				else:
					if HVMode == 2:
						board.WriteSetting("LowSideVoltage", 0x82400)

				kNPacketsPerEvent = 64 #One per channel
				#if multiple channels depend on FPGA settings
				kPacketSize = 86 + (numBlock-1)*64 #you can read it on wireshark
				# check for data size in bytes
				kBufferDepth = 300000

				print kBufferDepth*kPacketSize, "Bytes allocated for buffer"

				#Set up IO
				listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
				#target_driver.TargetModule.DataPortPing(my_ip, board_ip)#akira's hack
				listener.AddDAQListener(my_ip)
				listener.StartListening()

				writer = target_io.EventFileWriter(outFile, kNPacketsPerEvent, kPacketSize)
				buf = listener.GetEventBuffer()
				print numpy.size(buf)
				#time.sleep(random.randint(1,20))
				#time.sleep(5)

				#board.WriteSetting("TACK_EnableTrigger",0x10000)
	        		#board.WriteSetting("ExtTriggerDirection",1)

				if Trigger==0:
					ld.sendCmd("ALL OFF")
				else:
                	        	ld.sendCmd('FAST_PULSE ON')
                	        	ld.sendCmd("FREQ %s" % (Freq))
                	        	ld.sendCmd("BRIGHTNESS 4095")
                        		ld.sendCmd("AWG_SET 100")
                        		ld.sendCmd("TRIG_OUTPUT ON")

				#if ii:
				#	time.sleep(sleepBeforeRun)
				#	ii = 0
				#else:
				#	time.sleep(1)
				time.sleep(sleepBeforeRun)

				# MakeLog
				if makelog:
					logfilename = "%s/run%d.log" % (outdirname,runID)
                                        logfile = open(logfilename,'w')

					for addr in range(129):
						#print addr
						value = board.ReadRegister(addr)
						#print value[1]
						hexValue = "0x%08x" % value[1]
						hexAddress = "0x%02x" % addr
						currentTime = datetime.datetime.utcnow()
						line = "%s\t%s\t%s\n" % (currentTime, hexAddress, hexValue)
						logfile.write(line)
					logfile.close()
					print "%s written." % (logfilename)

				if Trigger==1:
					if TrackDataTakingTime:
						starttime = time.time()
					tester.EnableExternalTrigger(True)
                                        writer.StartWatchingBuffer(buf)
					time.sleep(runDuration)
                                        writer.StopWatchingBuffer()
					tester.EnableExternalTrigger(False)
					if TrackDataTakingTime:
						endtime = time.time()
						starttimesave.append(starttime)
						endtimesave.append(endtime)
					ld.sendCmd("ALL OFF")
				elif Trigger==0:	

					tester.EnableSoftwareTrigger(True)
					board.WriteSetting("Row",5)
					board.WriteSetting("Column",0)
					writer.StartWatchingBuffer(buf)	
					for i in range(runDuration*Freq):
						tester.SendSoftwareTrigger()
						time.sleep(1./Freq)
					writer.StopWatchingBuffer()
					tester.EnableSoftwareTrigger(False)
					if TrackDataTakingTime:
						endtime = time.time()
						starttimesave.append(starttime)
						endtimesave.append(endtime)
				elif Trigger==2:
		                        # get thresh values
		                        thresh=[[850,950,950,850],
		                                [850,1000,950,900],
		                                [800,900,700,600],
		                                [700,850,800,750]]
		                        #thresh=[[450,550,550,450],
		                        #       [250,600,550,500],
		                        #       [400,500,300,200],
		                        #       [200,450,400,350]]
		
		                        tuneModule.getTunedWrite(moduleID,board,Vped)
		                        tester.SetTriggerModeAndType(0b00, 0b00)
		                        deadtime=500 #in units of 8 ns
		                        triggerDly=580
	
		                        tester.SetTriggerDeadTime(deadtime)
		                        board.WriteSetting("TriggerDelay",triggerDly)
		                        for asic in range(4):
		                                for group in range(4):
		                                        tester.EnableTriggerCounterContribution(asic, group, False)
		                                        board.WriteASICSetting("Thresh_{}".format(group), asic, thresh[asic][group], True)
		                                        tester.EnableTrigger(asic,group,False)
		                        #enable internal trigger
		                        for asic in range(0,1):
		                                for group in range (0,1):
		                                        tester.EnableTriggerCounterContribution(asic, group, True)
		                                        if(asic!=1): tester.EnableTrigger(asic,group,True)
		                        ##time.sleep(30)                        
		                        #buf.Flush()
		                        writer.StartWatchingBuffer(buf)
		                        time.sleep(runDuration)
		                        writer.StopWatchingBuffer()
		
		                        for asic in range(4):
		                                for group in range(4):
	 	                                	tester.EnableTriggerCounterContribution(asic, group, False)
					ld.sendCmd("ALL OFF")
				if HVMode != 0:
					board.WriteSetting("HV_Enable", 0x0)

				print "finished data taking"
				#buf.Flush()
				writer.Close()
				##time.sleep(sleeptime)

	if PCMode == 1:
		bps.outputOff()
		if sleepPCMode:
		#	time.sleep(random.randint(20,30))
			time.sleep(0.1)
		else:
			time.sleep(sleepPCtime)	
	else:
		time.sleep(1)
	
	board.CloseSockets()
	tester.CloseSockets()

if TrackDataTakingTime:
	print "mean data taking time=", numpy.mean(numpy.array(endtimesave)-numpy.array(starttimesave))
	print "sigma=", numpy.std(numpy.array(endtimesave)-numpy.array(starttimesave))

