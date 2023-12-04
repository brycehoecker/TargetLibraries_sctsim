import target_driver
import time
import target_io
import run_control
import BrickPowerSupply
import numpy
# import tuneModule # if using Internal trigger, import this


Trigger = 1 # External=1 Software=0 Internal=2
HVMode = 0 # 1 if HV is activated

numBlock = 14
Vped = 2000
Freq = 300 # in Hz
runDuration = 10 # in second

my_ip = "192.168.1.2"
tb_ip = "192.168.1.173"
board_ip = "192.168.0.173"
board_def = "/Users/twu58/TargetDriver/trunk/config/TM7_FPGA_Firmware0xB0000100.def"
asic_def = "/Users/twu58/TargetDriver/trunk/config/TM7_ASIC.def"

board = target_driver.TargetModule(board_def, asic_def, 1)

# Establish slow control, if return nonzero value, power cycle and reinitialize
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

if HVMode:
	print board.WriteSetting("HV_Enable", 0x1)
	time.sleep(0.1)
	board.WriteRegister(0x20, 0x7300080F)
	board.WriteRegister(0x20, 0x7300080F)
	time.sleep(1)
	board.WriteRegister(0x20, 0x8280080F)

kNPacketsPerEvent = 64
kPacketSize = 86 + (numBlock-1)*64
kBufferDepth = 3000
listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
listener.AddDAQListener(my_ip)
listener.StartListening()
writer = target_io.EventFileWriter(outFile, kNPacketsPerEvent, kPacketSize)
buf = listener.GetEventBuffer()

time.sleep(30)

if Trigger == 1:
	tester.EnableExternalTrigger(True)
	writer.StartWatchingBuffer(buf)
	time.sleep(runDuration)
	writer.StopWatchingBuffer()
	tester.EnableExternalTrigger(False)
elif Trigger == 0:
	tester.EnableSoftwareTrigger(True)
	writer.StartWatchingBuffer(buf)
	for i in range(runDuration*Freq):
		tester.SendSoftwareTrigger()
		time.sleep(1./Freq)
	writer.StopWatchingBuffer()
	tester.EnableSoftwareTrigger(False)
elif Trigger == 2:
	thresh=[[850,950,950,850],
		[850,1000,950,900],
		[800,900,700,600],
		[700,850,800,750]]
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
	                writer.StartWatchingBuffer(buf)
	                time.sleep(runDuration)
	                writer.StopWatchingBuffer()
	
	                for asic in range(4):
	                	for group in range(4):
	                        	tester.EnableTriggerCounterContribution(asic, group, False)
buf.Flush()
writer.Close()
time.sleep(1)

board.CloseSockets()
tester.CloseSockets()	
