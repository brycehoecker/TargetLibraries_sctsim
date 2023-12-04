import target_driver
import target_io
import time
import numpy as np
import pdb
import os

outdir = "/home/cta/luigi/TC_EvalBoard/data/20160620/TF_TD250_4b/"
os.mkdir(outdir)

Vped_DAC = np.arange(495,4096,20)
#Vped_DAC = np.arange(495,499,2)

my_ip = "192.168.0.1"
board_ip = "192.168.0.123"
#board_def = "/home/cta/TARGET/TargetDriver/config/TEC_FPGA_Firmware0xFEDA0003.def"
board_def = "/home/cta/TARGET/TargetDriver/config/TECT5TEA_FPGA_Firmware0xFEDA0008.def"
asic_def = "/home/cta/TARGET/TargetDriver/config/TEC_ASIC.def"
trigger_asic_def = "/home/cta/TARGET/TargetDriver/config/T5TEA_ASIC.def"

#board = target_driver.TargetModule(board_def, asic_def, 0)  # trigger_asic_def, 0)
#board.ReconnectToServer(my_ip, 8201, board_ip, 8105)
board = target_driver.TargetModule(board_def, asic_def, trigger_asic_def, 0)
board.ReconnectToServer(my_ip, 8201, board_ip, 8105)


#Enable synchronous trigger mode
board.WriteSetting("TriggerDelay", 250)
board.WriteSetting("TACK_TriggerType", 0x0)
board.WriteSetting("TACK_TriggerMode", 0x0)
board.WriteSetting("TACK_EnableTrigger", 0x10000)
#Enable all 16 channels and enable zero supression
board.WriteSetting("EnableChannelsASIC0", 0xffff)
board.WriteSetting("Zero_Enable", 0x1)


board.WriteSetting("NumberOfBlocks", 3)
# last block not usable according to Manuel note

board.WriteSetting("ExtTriggerDirection", 0x1)  # switch on sync trigger

#pdb.set_trace()

kNPacketsPerEvent = 16#reading only one channel
#if multiple channels depend on FPGA settings
kPacketSize = 278#you can read it on wireshark
# check for data size in bytes
kBufferDepth = 1000


for Vped in Vped_DAC:
    board.WriteSetting("Vped_value", int(Vped))
    time.sleep(1)
    board.WriteSetting("ExtTriggerDirection", 0x1)  # switch on sync trigger

    listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
    target_driver.TargetModule.DataPortPing(my_ip, board_ip)  # akira's hack
    listener.AddDAQListener(my_ip)
    listener.StartListening()

    outfile = outdir + "TFdata_VpedDAC_{:04d}.fits".format(Vped)
    print "taking data for Vped {} DAC".format(Vped)
    writer = target_io.EventFileWriter(outfile, kNPacketsPerEvent, kPacketSize)
    buf = listener.GetEventBuffer()
    writer.StartWatchingBuffer(buf)

    time.sleep(3)

    writer.StopWatchingBuffer()
    print "data taken"
    writer.Close()
    buf.Flush()
    listener.StopListening()
    board.WriteSetting("ExtTriggerDirection", 0x0)



board.CloseSockets()


# for Vped in Vped_DAC:
#     board.WriteSetting("Vped_value", int(Vped))
#     time.sleep(0.5)
#     outfile = outdir+"TFdata_VpedDAC_{:04d}.fits".format(Vped)
#     print "taking data for Vped {} DAC".format(Vped)
#
#     writer = target_io.EventFileWriter(outfile, kNPacketsPerEvent, kPacketSize)
#     writer.StartWatchingBuffer(buf)
#
#     time.sleep(2)
#
#     writer.StopWatchingBuffer()
#     time.sleep(0.5)
#     writer.Close()






