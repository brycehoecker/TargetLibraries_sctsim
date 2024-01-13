import target_driver
import target_io
import time
from astropy.io import ascii
import os
import sys

outfile = "/media/cta/157bfe11-9587-4947-8a3e-1e814c5c25dc/Messungen_Stefan/Raw/pedestal_r0.tio"

VPED_FILE = "/media/cta/157bfe11-9587-4947-8a3e-1e814c5c25dc/Messungen_Stefan/Config/Vpeds.txt"

VTRIM_FILE = "/media/cta/157bfe11-9587-4947-8a3e-1e814c5c25dc/Messungen_Stefan/Config/vtrim_scan.txt"

my_ip = "192.168.12.1"
module_ip = "192.168.12.173"
initialize = False

module_def = "/home/cta/Software/TargetDriver/trunk/config/TC_MSA_FPGA_Firmware0xC0000009.def"
asic_def = "/home/cta/Software/TargetDriver/trunk/config/TC_ASIC.def"
trigger_asic_def = "/home/cta/Software/TargetDriver/trunk/config/T5TEA_ASIC.def"

module = target_driver.TargetModule(module_def, asic_def, trigger_asic_def, 0)
if initialize:
    module.EstablishSlowControlLink(my_ip, module_ip)
    module.Initialise()
    module.EnableDLLFeedback()
    print ("module initialized")
else:
    module.ReconnectToServer(my_ip, 8201, module_ip, 8105)

ret, fw = module.ReadRegister(0)
print ("Firmware version: {:x}".format(fw))

module.DisableHVAll()#disable all for safety, atm turn on by default

### Setting VPEDs ###
with open(VPED_FILE) as f:
  content = f.readlines()
content = [x.strip() for x in content]
print("Setting VPEDs to")
for asic in range(4):
  module.WriteTriggerASICSetting("VpedBias", asic, 1800, True)
  for channel in range(16):
    print(str(asic) + "   " + str(channel) + "   " + str(asic*16+channel) + "   " + str(content[asic*16+channel]))
    module.WriteTriggerASICSetting("Vped_{}".format(channel), asic, int(content[asic*16+channel]), True)
time.sleep(1)

### Setting optimized SSToutFB & VtrimT ###
data = ascii.read(VTRIM_FILE)
print(data)
for asics in range(4):
  print("Setting SSToutFB_Delay of Asic " + str(asics) + " to " + str(int(data[asics][2])))
  module.WriteASICSetting("SSToutFB_Delay", asics, int(data[asics][2]), True, False) # standard value: 58
  print("Setting VtrimT of Asic " + str(asics) + " to " + str(int(data[asics+4][2])))
  module.WriteASICSetting("VtrimT", asics, int(data[asics+4][2]), True, False) # standard value: 1240 
time.sleep(1)

for asic in range(4):
    module.WriteSetting("EnableChannelsASIC{}".format(asic), 0xffff)
module.WriteSetting("Zero_Enable", 0x1)
module.WriteSetting("DoneSignalSpeedUp",0)
nblocks = 8
module.WriteSetting("NumberOfBlocks", nblocks-1)
module.WriteSetting("MaxChannelsInPacket", 4)

module.WriteSetting("TACK_TriggerType", 0x0)
module.WriteSetting("TACK_TriggerMode", 0x0)

module.WriteSetting("SlowADCEnable_Power",1)

### let module head up a bit ###
module.WriteSetting("ExtTriggerDirection", 0x1) # hardsync
module.WriteSetting("TACK_EnableTrigger", 0x10000)
print("Wait 5 mins to stabilise")
for i in range(2):
	######### Read Temperatures #############
	print("\n------ Waited {}s -------".format(i*5))
	ret,temp =  module.GetTempI2CPrimary()
	print ("Temperature Pri: ",temp)
	ret, temp =  module.GetTempI2CAux()
	print ("Temperature Aux: ",temp)
	ret, temp =  module.GetTempI2CPower()
	print ("Temperature Pow: ",temp)
	ret, temp =  module.GetTempSIPM()
	print ("Temperature Camera: {:3.2f}".format(temp))
	time.sleep(5)
module.WriteSetting("TACK_EnableTrigger", 0)
time.sleep(1)
kNPacketsPerEvent = 16
# by default we have a data packet for each channel, this can be changed
kPacketSize = target_driver.DataPacket_CalculatePacketSizeInBytes(4, 32 * (nblocks))
kBufferDepth = 10000

listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
listener.AddDAQListener(my_ip)
listener.StartListening()
writer = target_io.EventFileWriter(outfile, kNPacketsPerEvent, kPacketSize)
buf = listener.GetEventBuffer()
writer.StartWatchingBuffer(buf)

####start data taking



for i in range(0,128):
	module.WriteSetting("TriggerDelay", i*32+26)
	module.WriteSetting("TACK_EnableTrigger", 0x10000)  # hardware trigger
	print("\n------ Delay is {}ns -------".format(i*32+26))
	ret,temp =  module.GetTempI2CPrimary()
	print ("Temperature Pri: ",temp)
	ret, temp =  module.GetTempI2CAux()
	print ("Temperature Aux: ",temp)
	ret, temp =  module.GetTempI2CPower()
	print ("Temperature Pow: ",temp)
	ret, temp =  module.GetTempSIPM()
	print ("Temperature Camera: {:3.2f}".format(temp))
	time.sleep(0.2)  # wait 3 s to accumulate data
	module.WriteSetting("TACK_EnableTrigger", 0)

for i in range(0,128):
	module.WriteSetting("TriggerDelay", i*32+26+1)
	module.WriteSetting("TACK_EnableTrigger", 0x10000)  # hardware trigger
	print("\n------ Delay is {}ns -------".format(i*32+26+1))
	ret,temp =  module.GetTempI2CPrimary()
	print ("Temperature Pri: ",temp)
	ret, temp =  module.GetTempI2CAux()
	print ("Temperature Aux: ",temp)
	ret, temp =  module.GetTempI2CPower()
	print ("Temperature Pow: ",temp)
	ret, temp =  module.GetTempSIPM()
	print ("Temperature Camera: {:3.2f}".format(temp))
	time.sleep(0.2)  # wait 3 s to accumulate data
	module.WriteSetting("TACK_EnableTrigger", 0)   # disable all triggers



time.sleep(1)

####close connection to module and output file
writer.StopWatchingBuffer()  # stops data storing in file


module.DisableHVAll()

module.CloseSockets()
buf.Flush()
writer.Close()

