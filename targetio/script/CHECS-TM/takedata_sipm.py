import target_driver
import target_io
import time

outfile = "/home/cta/luigi/CHECS-TM/data/20170502/test/test37.fits"
my_ip = "192.168.12.1"
module_ip = "192.168.12.173"
initialize = True

module_def = "/home/cta/Software/TargetDriver/branches/issue17073/config/TC_MSA_FPGA_Firmware0xC0000003.def"
asic_def = "/home/cta/Software/TargetDriver/branches/issue17073/config/TC_ASIC.def"
trigger_asic_def = "/home/cta/Software/TargetDriver/branches/issue17229/config/T5TEA_ASIC.def"

module = target_driver.TargetModule(module_def, asic_def, trigger_asic_def, 0)
module.ReconnectToServer(my_ip, 8201, module_ip, 8105)


ret, fw = module.ReadRegister(0)
print "Firmware version: {:x}".format(fw)

for asic in range(4):
    module.WriteTriggerASICSetting("VpedBias",asic, 1800,True)
    for channel in range(16):
        module.WriteTriggerASICSetting("Vped_{}".format(channel),asic,1000,True)

for asic in range(4):
    module.WriteSetting("EnableChannelsASIC{}".format(asic), 0xffff)
module.WriteSetting("Zero_Enable", 0x1)
module.WriteSetting("DoneSignalSpeedUp",1)
nblocks = 7
module.WriteSetting("NumberOfBlocks", nblocks)

for superpixel in range(16):
    module.SetHVDAC(superpixel,55)
module.EnableHVAll()
print "let HV settle"
time.sleep(10)

kNPacketsPerEvent = 64
# by default we have a data packet for each channel, this can be changed
kPacketSize = target_driver.DataPacket_CalculatePacketSizeInBytes(1, 32 * (nblocks + 1))
kBufferDepth = 1000
listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
listener.AddDAQListener(my_ip)
listener.StartListening()
writer = target_io.EventFileWriter(outfile, kNPacketsPerEvent, kPacketSize)
buf = listener.GetEventBuffer()
writer.StartWatchingBuffer(buf)

####start data taking
module.WriteSetting("TriggerDelay", 4000)
# lookback time between instant when the trigger is issued and the portion of the ASIC storage to digitize
module.WriteSetting("TACK_TriggerType", 0x0)
module.WriteSetting("TACK_TriggerMode", 0x0)
# normal trigger operations
module.WriteSetting("ExtTriggerDirection", 0x0)  # hard trigger from external source
module.WriteSetting("TACK_EnableTrigger", 0x10000)  # hardware trigger

time.sleep(3)  # wait 3 s to accumulate data

####stops data taking
module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers

module.DisableHVAll()

####close connection to module and output file
writer.StopWatchingBuffer()  # stops data storing in file
module.CloseSockets()
buf.Flush()
writer.Close()
