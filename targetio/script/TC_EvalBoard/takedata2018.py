import target_driver
import target_io
import time
import pdb



#only after power up
initialize = True


#lookbacktime
triggerdelay=485
#360 fits for 4 blocks external trigger at ECAP Box setup, 485 for internal trigger

#analog sum offset
pmtref4=0

#triggerthreshold
thresh=4000

#triggermask, bits 0-3 triggergroups 0-3, bit 16 = external/hardsync
trigenable=0x10000 #external
#trigenable=0b00000000000000001 #group 0

#trigger direction (1=hardsync,0=external)
trigdir=0

#width of trigger signal, 985 ~ 20ns (larger -> signal more narrow)
wbias=985
#Number of readout blocks (32 samples each)
nblocks=4

#deadtime in us
deadtime=100

#measurement time in seconds
measuretime = 100

#outfile
outfile = "pedestal_r0.tio"

#path to def files
defdir = "/home/cta/Software/TargetDriver/trunk/config"

#computer ip
my_ip = "192.168.0.1"

#eval board ip
board_ip = "192.168.0.123"

board_def = defdir+"/TC_EB_FPGA_Firmware0xFEDA001C.def"
asic_def = defdir+"/TC_ASIC.def"
trigger_asic_def = defdir+"/T5TEA_ASIC.def"


board = target_driver.TargetModule(board_def, asic_def, trigger_asic_def, 0)
if initialize:
    board.EstablishSlowControlLink(my_ip, board_ip)
    board.Initialise()
    board.EnableDLLFeedback()
    #board.WriteSetting("SetDataPort", 8107)
    #board.WriteSetting("SetSlowControlPort", 8201)
else:
    board.ReconnectToServer(my_ip, 8201, board_ip, 8105)


#Set Vped
for channel in range(16):
    board.WriteTriggerASICSetting("Vped_{}".format(channel),0, 1500,True)

#Write Trigger Threshold settings
board.WriteTriggerASICSetting("PMTref4_0", 0,pmtref4, True)
board.WriteTriggerASICSetting("Thresh_0", 0, thresh, True)
board.WriteTriggerASICSetting("PMTref4_1", 0,pmtref4, True)
board.WriteTriggerASICSetting("Thresh_1", 0, thresh, True)
board.WriteTriggerASICSetting("PMTref4_2", 0,pmtref4, True)
board.WriteTriggerASICSetting("Thresh_2", 0, thresh, True)
board.WriteTriggerASICSetting("PMTref4_3", 0,pmtref4, True)
board.WriteTriggerASICSetting("Thresh_3", 0,thresh, True)

#Increase Trigger signal width (needed for eval board and stand alone)
board.WriteTriggerASICSetting("Wbias_0", 0,wbias, True)
board.WriteTriggerASICSetting("Wbias_1", 0,wbias, True)
board.WriteTriggerASICSetting("Wbias_2", 0,wbias, True)
board.WriteTriggerASICSetting("Wbias_3", 0,wbias, True)

#disable trigger at beginning
board.WriteSetting("TACK_EnableTrigger", 0)

#Set single trigger group for test
board.WriteTriggerASICSetting("PMTref4_0", 0,2150, True)
board.WriteTriggerASICSetting("Thresh_0", 0, 2000, True)


board.WriteSetting("TriggerDelay", triggerdelay)
board.WriteSetting("TACK_TriggerType", 0x0)
board.WriteSetting("TACK_TriggerMode", 0x0)

#change ramp parameters
board.WriteASICSetting("Isel", 0, 2200, True)
board.WriteASICSetting("Vdischarge", 0, 850, True)

#Enable all 16 channels and enable zero supression. Zero suppression needs to be always on. Suppresses disabled channels (in eval board case 16-63).
board.WriteSetting("EnableChannelsASIC0", 0xFFFF)				
board.WriteSetting("Zero_Enable", 0x1)

#Enable done bit i(if enabled, undefined timing between ramps)
board.WriteSetting("DoneSignalSpeedUp",0);


board.WriteSetting("NumberOfBlocks", nblocks-1)

#deadtime settings

#Dead time after trigger in x8ns
deadtimenano=deadtime*1000/8
if (deadtimenano>0xFFFF):
    print("deadtime to large!")
    exit()
board.WriteSetting("DurationofDeadtime",int(deadtimenano))

#disable triggers while serial readout of TC (needed for internal trigger due to bad layout)
board.WriteSetting("SR_DisableTrigger", 1)

board.WriteSetting("ExtTriggerDirection", trigdir) 

#number of packets/events. 16 means one channel/packet
kNPacketsPerEvent = 16#reading only one channel

#you can read it on wireshark, also a function is availiable to calculate this from nblocks and channels/packet
kPacketSize = 278

#Event buffer in PC memory
kBufferDepth = 10000



#start data listener
listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
listener.AddDAQListener(my_ip)
listener.StartListening()

#start writer
writer = target_io.EventFileWriter(outfile, kNPacketsPerEvent, kPacketSize)
buf = listener.GetEventBuffer()
writer.StartWatchingBuffer(buf)


board.WriteSetting("TACK_EnableTrigger", trigenable)

time.sleep(measuretime)

board.WriteSetting("TACK_EnableTrigger", 0)

time.sleep(.5)

writer.StopWatchingBuffer()

board.CloseSockets()
buf.Flush()
writer.Close()



