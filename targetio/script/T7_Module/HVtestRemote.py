import target_driver
import time
import target_io
import run_control
import BrickPowerSupply
import numpy
#import argparse
import random
from LED import *

ld=LED()

#minVped = 125
#maxVped = 4061+1
#stepVped = 164
#VpedList = numpy.concatenate([range(minVped,maxVped,stepVped),range(minVped,maxVped,stepVped),range(minVped,maxVped,stepVped),range(minVped,maxVped,stepVped),range(minVped,maxVped,stepVped)])
#VpedList = range(minVped,maxVped,stepVped)
#VpedList = [2000,2000,2000,2000,2000]
#VpedList = [1000]
VpedList = [2000]*10

#Vped = 2000

FreqList = range(30,105,5)

#runDuration = 1
#runDurationList = [1,3,10]

runDuration = 10

#sleepDurationList = [44.32]
#sleepDurationList = [42,42.5,43,43.5,44,44.5,45,45.5,46,46.5,47]
#sleepDurationList = [44.27]
#sleepDurationList = range(0,65,5)

#sleeptimeList = [5]

sleeptime = 5

sleepDurationList = [30]

remote = 1
Ext = 1
PCifFail = 0
#InitOnce = 1
timesave = []
HV = 0
numBlock = 2


#for Vped in VpedList:
for sleepDuration in sleepDurationList:

	#for sleeptime in sleeptimeList:
	for Freq in FreqList:
		if remote:
			InitFail = 1
			while InitFail != 0:
				bps = BrickPowerSupply.BrickPowerSupply('2200','/dev/tty.usbserial')
				time.sleep(0.5)
				bps.open()
				bps.outputOn()
				#bps.setVoltage(12)
				#bps.setMaxCurrent(2.2)
				time.sleep(30)
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
        			board = target_driver.TargetModule(board_def, asic_def, 1)
        			InitFail = board.EstablishSlowControlLink(my_ip, board_ip)
				print(InitFail)
				if InitFail:
					bps.outputOff()
					time.sleep(15)

		elif PCifFail:
			InitFail = 1
        	        while InitFail != 0:
        	                bps = BrickPowerSupply.BrickPowerSupply('2200','/dev/tty.usbserial')
        	                time.sleep(0.5)
        	                bps.open()
        	                #bps.outputOn()
        	                #bps.setVoltage(12)
        	                #bps.setMaxCurrent(2.2)
        	                #time.sleep(30)
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
        	                board = target_driver.TargetModule(board_def, asic_def, 1)
        	                InitFail = board.EstablishSlowControlLink(my_ip, board_ip)
        	                print(InitFail)
        	                if InitFail:
        	                        bps.outputOff()
        	                        time.sleep(15)
					bps.outputOn()
					time.sleep(30)


		else:
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
			board = target_driver.TargetModule(board_def, asic_def, 1)
			print board.EstablishSlowControlLink(my_ip, board_ip)

		time.sleep(0.1)
		print board.Initialise()

		#	hostname = run_control.getHostName()
		#	outdirname = run_control.getDataDirname(hostname)
		#	runID = run_control.incrementRunNumber(outdirname)
		#	outFile = "%srun%d.fits" % (outdirname,runID)
		#	print "Writing to: %s" % outFile

		time.sleep(0.1)
		tester = target_driver.TesterBoard()
		tester.Init(my_ip, tb_ip)
		time.sleep(0.1)
		tester.EnableReset(True)
		time.sleep(0.1)
		tester.EnableReset(False)
		time.sleep(0.1)

		##board.WriteSetting("TACK_EnableTrigger",0b010000000000000000)
		##board.WriteSetting("ExtTriggerDirection",0)
		time.sleep(0.5)

		#for sleepDuration in sleepDurationList:
		for Vped in VpedList:
		#for Freq in FreqList:
        		hostname = run_control.getHostName()
        		outdirname = run_control.getDataDirname(hostname)
        		runID = run_control.incrementRunNumber(outdirname)
        		outFile = "%srun%d.fits" % (outdirname,runID)
        		print "Writing to: %s" % outFile

			#Set Vped, enable all channels for readout
			board.WriteSetting("Vped_value", Vped)
			board.WriteSetting("EnableChannelsASIC0", 0xffff)
			board.WriteSetting("EnableChannelsASIC1", 0xffff)
			board.WriteSetting("EnableChannelsASIC2", 0xffff)
			board.WriteSetting("EnableChannelsASIC3", 0xffff)
			board.WriteSetting("Zero_Enable", 0x1)
	
			board.WriteSetting("NumberOfBlocks", numBlock-1)
			board.WriteSetting("TriggerDelay", 8)

			if HV:

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

			kNPacketsPerEvent = 64 #One per channel
			#if multiple channels depend on FPGA settings
			kPacketSize = 86 + (numBlock-1)*64 #you can read it on wireshark
			# check for data size in bytes
			kBufferDepth = 3000

			#Set up IO
			listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
			#target_driver.TargetModule.DataPortPing(my_ip, board_ip)#akira's hack
			listener.AddDAQListener(my_ip)
			listener.StartListening()

			writer = target_io.EventFileWriter(outFile, kNPacketsPerEvent, kPacketSize)
			buf = listener.GetEventBuffer()

			#time.sleep(random.randint(1,20))
			#time.sleep(5)

			#board.WriteSetting("TACK_EnableTrigger",0x10000)
	        	#board.WriteSetting("ExtTriggerDirection",1)

			if Ext:
                        	ld.sendCmd('FAST_PULSE ON')
                        	ld.sendCmd("FREQ %s" % (Freq))
                        	ld.sendCmd("BRIGHTNESS 4095")
                        	ld.sendCmd("AWG_SET 100")
                        	ld.sendCmd("TRIG_OUTPUT ON")
                	else:
                        	ld.sendCmd("ALL OFF")

			time.sleep(sleepDuration)

			if Ext:
				tester.EnableExternalTrigger(True)
				writer.StartWatchingBuffer(buf)
				time.sleep(runDuration)
				writer.StopWatchingBuffer()
				tester.EnableExternalTrigger(False)


				endtime = time.time()
				print(endtime)
				timesave.append(endtime)
				ld.sendCmd("ALL OFF")
			else:
				#Enable external trigger
				#tester.EnableExternalTrigger(True)
	
				tester.EnableSoftwareTrigger(True)
	
				board.WriteSetting("Row",5)
				board.WriteSetting("Column",0)
		
				writer.StartWatchingBuffer(buf)
	
				#Taking data now
	
				for i in range(runDuration*300):
	
					tester.SendSoftwareTrigger()
					time.sleep(1/300.)
	
				#time.sleep(1)

				writer.StopWatchingBuffer()

				#Stop trigger
				#tester.EnableExternalTrigger(False)

				tester.EnableSoftwareTrigger(False)

				##board.WriteSetting("HV_Enable", 0x0)
				#Close everything

			if HV:
				board.WriteSetting("HV_Enable", 0x0)

			#listener.StopListening()

			#board.CloseSockets()
			#tester.CloseSockets()
			buf.Flush()
			writer.Close()
			time.sleep(sleeptime)

		if remote:
			bps.outputOff()
			#time.sleep(random.randint(20,30))
		#	for sleept in range(600):
                 #       	print "taking data now, next run in %d s" % (600-sleept)    
                  #      	time.sleep(1)
			time.sleep(600)

		else:
			time.sleep(5)
			#for sleeptime in range(1800):
			#	print "taking data now, next run in %d s" % (1800-sleeptime)	
			#	time.sleep(1)

			#time.sleep(20)
			#else:
			#time.sleep(5)
			#time.sleep(3)
			#time.sleep(random.randint(5,25))
			#time.sleep(5)
	
		board.CloseSockets()
		tester.CloseSockets()
	
		#print(timesave)
