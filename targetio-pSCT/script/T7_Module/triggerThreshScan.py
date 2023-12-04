import target_driver
import os
import time,datetime
import target_io
import run_control
#import BrickPowerSupply
import numpy
#import argparse
import random
import tuneModule

minVped = 125
maxVped = 4061+1
stepVped = 164
#VpedList = numpy.concatenate([range(minVped,maxVped,stepVped),range(minVped,maxVped,stepVped),range(minVped,maxVped,stepVped),range(minVped,maxVped,stepVped),range(minVped,maxVped,stepVped)])
#VpedList = range(minVped,maxVped,stepVped)
#VpedList = [2000,2000,2000,2000,2000]
#VpedList = [1000]*2
VpedList = [1106]
runDuration = 1

#trigger options {0:software, 1:external, 2:internal (self)
Trigger = 2

# only matters when running internal trigger
moduleID = 111

singlePixel=0
#runDuration = 1
#runDurationList = [1,3,10]

#runDuration = 1

timestamp = time.time()
dataset = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M')

doEff = 0

# set to 1 if looking at trigger efficiencies
efficiencyRun = 1
threshvals = numpy.arange(300,2600,50)
elapsed = 1.0 # run duration in seconds
duration = elapsed / 8.e-9 # elapsed s / 8 ns => duration time of counting in 8 ns 
inputf = 100 # frequency of LED flasher in hz
timeint = int(duration)

def efficiency(tester):
	tester.StartTriggerEfficiencyCounter(timeint)
	while not tester.IsTriggerEfficiencyCounterOutsideDeadTimeCompleted():
		time.sleep(0.05)
	count = tester.GetTriggerEfficiencyCounterOutsideDeadTime()
	eff = count/(inputf*elapsed)
	return eff

def trigCount(tester):
	tester.StartTriggerEfficiencyCounter(timeint)
	while not tester.IsTriggerEfficiencyCounterOutsideDeadTimeCompleted():
		time.sleep(0.05)
	time.sleep(0.2)
	#print "get Efficiency now!"
	count = tester.GetTriggerEfficiencyCounterOutsideDeadTime()
	return count

sleepDurationList = [5]
#sleepDurationList = [14.32]
#sleepDurationList = [42,42.5,43,43.5,44,44.5,45,45.5,46,46.5,47]
#sleepDurationList = [44.27]
#sleepDurationList = [14.32]

remote = 0
PCifFail = 1
InitOnce = 1
timesave = []
HV = 1
numBlock = 2

my_ip = "192.168.1.2"
tb_ip = "192.168.1.173"
board_ip = "192.168.0.173"
board_def = "/Users/pkarn/TargetDriver/config/TM7_FPGA_Firmware0xB0000100.def"
asic_def = "/Users/pkarn/TargetDriver/config/TM7_ASIC.def"


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

	####board.WriteSetting("TACK_EnableTrigger",0b001111111111111111)
	##board.WriteSetting("ExtTriggerDirection",0)
time.sleep(0.5)

##print "Trigger mode board: ", board.GetTriggerMode()
print "Trigger mode tester: ", tester.GetTriggerMode()

for sleepDuration in sleepDurationList:

	for Vped in VpedList:

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
			#board.WriteRegister(0x20, 0x7300080F)
			#board.WriteRegister(0x20, 0x7300080F)
			board.WriteSetting("HV_Enable", 0b1)   #enable distribution from BP
			board.WriteSetting("SelectLowSideVoltage",0b1) #not sure what this does
			board.WriteSetting("HVDACControl",0b1111)      #selects all ASICs
			board.WriteSetting("LowSideVoltage",0x73000)   #enable HV with 4.096 V reference (most significant 5 nibbles: 29,440 counts)
			board.WriteSetting("LowSideVoltage",0x82800)	#set low side to 2.048 V (0x800 DAC counts) across all pixels

			if(singlePixel):
				nasics = 4
				npxls = 4
				asicDict = {0 : 0b0001, 1 : 0b0010, 2 : 0b0100, 3 : 0b1000}
				codeload = 0x30000	# 0011 is coden_loadn and allows the writing of a trim voltage to a single trigger pixel

				# choose the pixel to leave open
				openASIC = 0
				openPxl = 0
	
				# writes the trim voltage of all other pixels to their max values (of 4.096 V)
				for asic in range(nasics):
					board.WriteSetting("HVDACControl", asicDict[asic])
					for pxl in range(npxls):
						if( (asic != openASIC) or (pxl != openPxl) ):
							trigPxl = int("0x{}000".format(pxl),16)
							trimVoltage = 0xFFF
							print (codeload|trigPxl|trimVoltage)
							board.WriteSetting("LowSideVoltage", (codeload | trigPxl | trimVoltage))

				# writes the trim voltage of that specific value to 2.048 V
				board.WriteSetting("HVDACControl", asicDict[openASIC])
				trigPxl = int("0x{}000".format(openPxl),16)
				trimVoltage = 0x800
				board.WriteSetting("LowSideVoltage", (codeload | trigPxl | trimVoltage))



				time.sleep(1)
			else:
				#Set low side voltage for all trigger channels to 2.048V
				board.WriteRegister(0x20, 0x8280080F)

		kNPacketsPerEvent = 64 #One per channel
		#if multiple channels depend on FPGA settings
		kPacketSize = 86 + (numBlock-1)*64 #you can read it on wireshark
		###kPacketSize = 918
		# check for data size in bytes
		kBufferDepth = 3000

		#Set up IO
		#listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
		#target_driver.TargetModule.DataPortPing(my_ip, board_ip)#akira's hack
		#listener.AddDAQListener(my_ip)
		#listener.StartListening()

		#writer = target_io.EventFileWriter(outFile, kNPacketsPerEvent, kPacketSize)
		#buf = listener.GetEventBuffer()

		#tbleTriggerime.sleep(random.randint(1,20))
		time.sleep(10)

		#board.WriteSetting("TACK_EnableTrigger",0x10000)
	        #board.WriteSetting("ExtTriggerDirection",0)
		#board.WriteSetting("Row",5)
		#board.WriteSetting("Column",0)
		##board.WriteSetting("TACK_TriggerMode",01)

		# external trigger
		if Trigger==1:
			tester.EnableExternalTrigger(True)
			writer.StartWatchingBuffer(buf)
			time.sleep(runDuration)

		#	board.WriteSetting("TACK_EnableTrigger",0)

			writer.StopWatchingBuffer()
			tester.EnableExternalTrigger(False)
			#tester.SetTriggerModeAndType(0b01,0b10)

			endtime = time.time()
			print(endtime)
			timesave.append(endtime)

									
		# software trigger
		elif Trigger==0:
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

		# internal trigger
		elif Trigger==2:
			if efficiencyRun:
				effout = outdirname + 'triggerEfficiency/{}/'.format(dataset)
				try:
					os.mkdir(effout)
				except:
					print "directory", effout, "already exists"
			# get thresh values
			"""
			thresh=[[850,950,950,850],
				[850,1000,950,900],
				[800,900,700,600],
				[700,850,800,750]]
			#thresh=[[450,550,550,450],
			#	[250,600,550,500],
			#	[400,500,300,200],
			#	[200,450,400,350]]
			"""

			tuneModule.getTunedWrite(moduleID,board,Vped)
			deadtime=500 #in units of 8 ns
			triggerDly=580
			tester.SetTriggerModeAndType(0b00, 0b00)		

			tester.SetTriggerDeadTime(deadtime)
			board.WriteSetting("TriggerDelay",triggerDly)
			# disabling everything first
			for asic in range(4):
				for group in range(4):
					tester.EnableTriggerCounterContribution(asic, group, False)
					tester.EnableTrigger(asic,group,False)

			for asic in range(4):
				for group in range(4):		
					outname = 'a{}g{}.txt'.format(asic,group)
					effoutname = effout+outname
					print "saving in", effoutname
					outFile = open(effoutname, 'w')
					tester.EnableTriggerCounterContribution(asic,group,True)
					#tester.EnableTrigger(asic,group,True)
					Thresh_group = "Thresh_{}".format(group)
					for thresh in threshvals:
						board.WriteASICSetting(Thresh_group.format(group), asic, int(thresh), True)
						time.sleep(0.2)
						if doEff:
							eff = efficiency(tester)
						else:
							eff = trigCount(tester)
						print asic, group, int(thresh), eff
						outFile.write("%d %f\n"%(thresh, eff))
					outFile.close()
					#tester.EnableTrigger(asic,group,False)
					tester.EnableTriggerCounterContribution(asic, group, False)
			#time.sleep(30)			
			#buf.Flush()
			"""
			writer.StartWatchingBuffer(buf)
                        time.sleep(runDuration)
			writer.StopWatchingBuffer()
			"""
			for asic in range(4):
                                for group in range(4):
                                        tester.EnableTriggerCounterContribution(asic, group, False)


		if HV:
			board.WriteSetting("HV_Enable", 0x0)

		#listener.StopListening()

		#board.CloseSockets()
		#tester.CloseSockets()
		#buf.Flush()
		#writer.Close()
		if remote:
			bps.outputOff()
		if numpy.size(VpedList) == 1:
			time.sleep(0.1)
		else:
			if remote:
				time.sleep(20)
 			else:
				#time.sleep(5)
				#time.sleep(3)
				#time.sleep(random.randint(5,25))
				time.sleep(sleepDuration)
	
board.CloseSockets()
tester.CloseSockets()

print(timesave)

