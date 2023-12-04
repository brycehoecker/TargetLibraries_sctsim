import target_driver
import target_io
import time
import pdb
import argparse

def auto_int(x):
    return int(x, 0)

parser = argparse.ArgumentParser()
parser.add_argument("--initialize", help="Initialize the board", action="store_true", default=False)
parser.add_argument("-t", "--trigenable", help="Enable triggers (see def file TACK_EnableTrigger), default is 0x10000 = hardware trigger", type=auto_int, default=0x10000)
parser.add_argument("-d", "--trigdir", help="External trigger direction: 1 output (sync) 0 input (async, default)", type=int, default=0)
parser.add_argument("-f", "--filename", help="Name of output file", type=str, default="test.fits")
parser.add_argument("--Vped", help="Vped DAC value (applied to all channels)", type=int, default=1000)
parser.add_argument("--Thresh", help="Thresh value (see def file)", type=int, default=0)
parser.add_argument("--triggerdelay", help="Trigger delay in ns", type=int, default=224)
parser.add_argument("--PMTref4", help="PMTref4 (see def file)", type=int, default=1950)
parser.add_argument("--trigdeadtime", help="Deadtime enforced after each readout request (in 8 ns blocks)", type=int, default=0)
parser.add_argument("--directory", help="Output directory", type=str, default="./")
parser.add_argument("--defdir", help="Directory of the def files", type=str, default="./")
parser.add_argument("--SR_DisableTrigger", help="Disable triggering during serial readout of TC data", type=int, default=0)
args = parser.parse_args()

outdir = args.directory
outfile = outdir + "/" + args.filename
my_ip = "192.168.0.1"
board_ip = "192.168.0.123"

board_def = args.defdir+"/TC_EB_FPGA_Firmware0xFEDA0014.def"
asic_def = args.defdir+"/TC_ASIC.def"
trigger_asic_def = args.defdir+"/T5TEA_ASIC.def"

board = target_driver.TargetModule(board_def, asic_def, trigger_asic_def, 0)
if args.initialize:
    board.EstablishSlowControlLink(my_ip, board_ip)
    board.Initialise()
    #time.sleep(3)
    board.EnableDLLFeedback()
    #time.sleep(2)
    board.WriteSetting("SetDataPort", 8107)
    board.WriteSetting("SetSlowControlPort", 8201)
else:
    board.ReconnectToServer(my_ip, 8201, board_ip, 8105)


# #Set Vped
board.WriteTriggerASICSetting("VpedBias",0, 1800,True)
for channel in range(16):
    board.WriteTriggerASICSetting("Vped_{}".format(channel),0, args.Vped,True)

#set up trigger, just group 1, channel 4 for the moment
#board.WriteTriggerASICSetting("TriggerEnable_Ch4",0, 1,True)
#board.WriteTriggerASICSetting("TriggerEnable_Ch5",0, 1,True)
#board.WriteTriggerASICSetting("TriggerEnable_Ch6",0, 1,True)
#board.WriteTriggerASICSetting("TriggerEnable_Ch7",0, 1,True)
board.WriteTriggerASICSetting("PMTref4_2", 0,args.PMTref4, True)
board.WriteTriggerASICSetting("Thresh_2", 0, args.Thresh, True)

# #configure board for data taking
board.WriteSetting("TriggerDelay", args.triggerdelay)
board.WriteSetting("TACK_TriggerType", 0x0)
board.WriteSetting("TACK_TriggerMode", 0x0)
board.WriteSetting("TACK_EnableTrigger", args.trigenable)

#Enable all 16 channels and enable zero supression
board.WriteSetting("EnableChannelsASIC0", 0xffff)				
board.WriteSetting("Zero_Enable", 0x1)
#Enable done bit
board.WriteSetting("DoneSignalSpeedUp",1);

board.WriteSetting("NumberOfBlocks", 4)
# last block not usable according to Manuel note

#deadtime settings
board.WriteSetting("EnableDeadTimeLogic",1)
board.WriteSetting("DurationofDeadtime",args.trigdeadtime)
board.WriteSetting("SR_DisableTrigger", args.SR_DisableTrigger)

board.WriteSetting("ExtTriggerDirection", args.trigdir)  # switch on sync trigger

kNPacketsPerEvent = 16#reading only one channel
#if multiple channels depend on FPGA settings
kPacketSize = 342#you can read it on wireshark
# check for data size in bytes
kBufferDepth = 1000

listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
listener.AddDAQListener(my_ip)
listener.StartListening()

writer = target_io.EventFileWriter(outfile, kNPacketsPerEvent, kPacketSize)
buf = listener.GetEventBuffer()
writer.StartWatchingBuffer(buf)

time.sleep(3)

writer.StopWatchingBuffer()
board.WriteSetting("ExtTriggerDirection", 0x0)
board.WriteSetting("TACK_EnableTrigger", 0)

board.CloseSockets()
buf.Flush()
writer.Close()



