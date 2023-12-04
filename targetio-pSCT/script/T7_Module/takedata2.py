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
parser.add_argument("--directory", help="Directory where output files will be saved", type=str, default="./")
parser.add_argument("--triggerdelay", help="Trigger delay in ns", type=int, default=224)
parser.add_argument("--trigdeadtime", help="Deadtime enforced after each readout request (in 8 ns blocks)", type=int, default=0)
args = parser.parse_args()

outfile = args.directory+ '/' +args.filename
my_ip = "192.168.0.1"
board_ip = "192.168.0.173"

#board_def = "/home/cta/TARGET/TargetDriver/config/TEC_FPGA_Firmware0xFEDA0003.def"
board_def = "/home/cta/TARGET/TargetDriver/branches/issue14135/config/T7_MSA_FPGA_Firmware0xA0000102.def"
asic_def = "/home/cta/TARGET/TargetDriver/branches/issue14135/config/T7_ASIC.def"

board = target_driver.TargetModule(board_def, asic_def, 0)
if args.initialize:
    board.EstablishSlowControlLink(my_ip, board_ip)
    print board.Initialise()
    #time.sleep(3)
    board.EnableDLLFeedback()
    #time.sleep(2)
    board.WriteSetting("SetDataPort", 8107)
    board.WriteSetting("SetSlowControlPort", 8201)
else:
    board.ReconnectToServer(my_ip, 8201, board_ip, 8105)

# #Set Vped
board.WriteSetting("Vped_value", 2500)


# #configure board for data taking
board.WriteSetting("TriggerDelay", args.triggerdelay)
board.WriteSetting("TACK_TriggerType", 0x0)
board.WriteSetting("TACK_TriggerMode", 0x0)
board.WriteSetting("TACK_EnableTrigger", args.trigenable)

#Enable all 16 channels and enable zero supression
board.WriteSetting("EnableChannelsASIC0", 0xffff)	
board.WriteSetting("EnableChannelsASIC1", 0xffff)	
board.WriteSetting("EnableChannelsASIC2", 0xffff)	
board.WriteSetting("EnableChannelsASIC3", 0xffff)	
board.WriteSetting("Zero_Enable", 0x0)
#Enable done bit
#board.WriteSetting("DoneSignalSpeedUp",1);

nblocks=3
channelsinpacket=1
board.WriteSetting("NumberOfBlocks", nblocks-1)
board.WriteSetting("MaxChannelsInPacket", channelsinpacket)
# last block not usable according to Manuel note

#board.WriteSetting("EnableDeadTimeLogic",1)
#board.WriteSetting("DurationofDeadtime",args.trigdeadtime)
#board.WriteSetting("ExtTriggerDirection", args.trigdir)  # switch on sync trigger

kNPacketsPerEvent = 64#reading only one channel
#if multiple channels depend on FPGA settings
kPacketSize = target_driver.DataPacket.CalculatePacketSizeInBytes(channelsinpacket,nblocks*32)
kBufferDepth = 100000

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



