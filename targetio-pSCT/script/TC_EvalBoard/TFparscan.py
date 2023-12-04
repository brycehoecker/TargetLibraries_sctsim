import target_driver
import target_io
import time
import numpy as np
import pdb
import os

outdir_root = "/home/cta/luigi/TC_EvalBoard/data/20160705/testTF/"

try:
    os.mkdir(outdir_root)
except:
    pass

Vped_DAC = np.arange(495, 4096, 120)
# Vped_DAC = np.arange(495,499,2)

# parname = 'SBbias'
# parvals = np.arange(1920,1941,1)
# parname = "RampSignalDuration"
# parvals = np.arange(1050,1200,10)
# parASIC = False
# parname = "CMPbias"
# parvals = np.arange(1600,1750,10)
parname = "Isel"
parvals = np.arange(2300, 2301, 1)
# parname = "CMPbias"
# parvals = np.arange(1610,1631,1)
# parname = "CMPbias2"
# parvals = np.arange(710,731,1)
# parname = 'PUbias'
# parvals = np.arange(3010,3042,2)
parASIC = True

my_ip = "192.168.0.1"
board_ip = "192.168.0.123"

#board_def = "/home/cta/TARGET/TargetDriver/config/TEC_FPGA_Firmware0xFEDA0003.def"
board_def = "/home/cta/TARGET/TargetDriver/config/TECT5TEA_FPGA_Firmware0xFEDA0008.def"
asic_def = "/home/cta/TARGET/TargetDriver/config/TEC_ASIC.def"
trigger_asic_def = "/home/cta/TARGET/TargetDriver/config/T5TEA_ASIC.def"

#board = target_driver.TargetModule(board_def, asic_def, 0)  # trigger_asic_def, 0)
#board.ReconnectToServer(my_ip, 8201, board_ip, 8105)
board = target_driver.TargetModule(board_def, asic_def, trigger_asic_def, 0)
#board.ReconnectToServer(my_ip, 8201, board_ip, 8105)
board.EstablishSlowControlLink(my_ip, board_ip)
board.Initialise()
time.sleep(3)
board.EnableDLLFeedback()
time.sleep(2)
board.WriteSetting("SetDataPort", 8107)
board.WriteSetting("SetSlowControlPort", 8201)

# # # select alternative Wilkinson clock freq
# board.WriteSetting("WilkinsonClockFreq", 0b01)
# # # make V boundaries of ramp larger
# board.WriteASICSetting('SBbias', 0, 1934)
# # # shorten ramp
# board.WriteSetting("RampSignalDuration", 780)
# # # increase slew rate
# board.WriteASICSetting("Isel", 0, 2300)
# # #from rough scan
# board.WriteASICSetting("PUbias", 0, 3018)
# # #from rough scan
# board.WriteASICSetting("CMPbias", 0, 1620)
# board.WriteASICSetting("CMPbias2", 0, 726)

# Enable synchronous trigger mode
board.WriteSetting("TriggerDelay", 100)
board.WriteSetting("TACK_TriggerType", 0x0)
board.WriteSetting("TACK_TriggerMode", 0x0)
board.WriteSetting("TACK_EnableTrigger", 0x10000)
# #Set Vped
# board.WriteSetting("Vped_value", 2000)
# Enable one channel (Channel 0) and enable zero supression
board.WriteSetting("EnableChannelsASIC0", 0x1)				
board.WriteSetting("Zero_Enable", 0x1)

board.WriteSetting("NumberOfBlocks", 3)
# last block not usable according to Manuel note

# last block not usable according to Manuel note
kNPacketsPerEvent = 1  # reading only one channel
# if multiple channels depend on FPGA settings
kPacketSize = 278  # you can read it on wireshark
# check for data size in bytes
kBufferDepth = 1000

for parval in parvals:
    if parASIC:
        for s in range(1):
            board.WriteASICSetting(parname, 0, int(parval))
            time.sleep(2)
        print "changed", parname, "to", parval
    else:
        board.WriteSetting(parname, int(parval))
        print "change", parname, "to", parval
    outdir = outdir_root + '{}_{:04d}/'.format(parname, parval)
    os.mkdir(outdir)
    print "taking data for {} {} DAC".format(parname, parval)
    time.sleep(2)

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
