import target_driver
import target_io
import time
from astropy.io import ascii
import os
import sys
import random

outfile = "/media/cta/157bfe11-9587-4947-8a3e-1e814c5c25dc/Messungen_Stefan/Raw/file_0_r0.tio"

VPED_FILE = "/media/cta/157bfe11-9587-4947-8a3e-1e814c5c25dc/Messungen_Stefan/Config/Vpeds.txt"

VTRIM_FILE = "/media/cta/157bfe11-9587-4947-8a3e-1e814c5c25dc/Messungen_Stefan/Config/vtrim_scan.txt"

my_ip = "192.168.12.1"
module_ip = "192.168.12.173"
initialize = True

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

module.WriteSetting("TriggerDelay", 500) # lookback time between instant when the trigger is issued and the portion of the ASIC storage to digitize
module.WriteSetting("TACK_TriggerType", 0x0)
module.WriteSetting("TACK_TriggerMode", 0x0)

print ("\nEnabling Slow ADCs\n")
module.WriteSetting("SlowADCEnable_Primary",1)
module.WriteSetting("SlowADCEnable_Aux",1)
module.WriteSetting("SlowADCEnable_Power",1)

### switch on SiPM voltage
hval=[84,84,80,81,80,78,87,79,83,82,81,81,87,83,77,78]
for superpixel in range(13,14):
	module.SetHVDAC(superpixel,hval[superpixel])
	module.EnableHVSuperPixel(superpixel)
print ("let HV settle")
time.sleep(3)



######### Measure the HV DACs #############
def read_HVDAC():
  for channel in range (0,16) :
    ret, answer = module.ReadSetting("HV{}_Voltage".format(channel))
    if answer < 0x8000 :
      answer = answer + 0x8000
    else :
      answer = answer & 0x7FFF
    print ("HV SuperPixel {0} :\t{1:3.2f}".format(channel, answer *0.03815*2*20/1000))

read_HVDAC()

######### Measure Slow signal values #############
for channel in range (0,32) :
  ret, answer = module.ReadSetting("SlowResult{}_Primary".format(channel))
  if answer < 0x8000 :
    answer = answer + 0x8000
  else :
    answer = answer & 0x7FFF
  print ("Slow Primary Channel " , channel , " is " , answer * 0.03815*2)
print ("")
for channel in range (0,32) :
  ret, answer = module.ReadSetting("SlowResult{}_Aux".format(channel))
  if answer < 0x8000 :
    answer = answer + 0x8000
  else :
    answer = answer & 0x7FFF
  print ("Slow Auxiliary Channel " , channel , " is " , answer * 0.03815*2)


### let module head up a bit ###
module.WriteSetting("ExtTriggerDirection", 0x1) # hardsync
module.WriteSetting("TACK_EnableTrigger", 0x10000)
print("\nWait 5 mins to stabilise")
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

module.WriteSetting("TACK_EnableTrigger", 0x10000)  # hardware trigger

for i in range(2):
	######### Read Temperatures #############
	print("\n------ Took data for {}s -------".format(i*5))
	ret,temp =  module.GetTempI2CPrimary()
	print ("Temperature Pri: ",temp)
	ret, temp =  module.GetTempI2CAux()
	print ("Temperature Aux: ",temp)
	ret, temp =  module.GetTempI2CPower()
	print ("Temperature Pow: ",temp)
	ret, temp =  module.GetTempSIPM()
	print ("Temperature Camera: {:3.2f}".format(temp))
	time.sleep(5)
        
#	for j in range(100):
#		module.WriteSetting("TriggerDelay",random.randint(0,4095))
#		time.sleep(0.05)
####stops data taking
module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers

time.sleep(1)

####close connection to module and output file
writer.StopWatchingBuffer()  # stops data storing in file


module.DisableHVAll()

module.CloseSockets()
buf.Flush()
writer.Close()

