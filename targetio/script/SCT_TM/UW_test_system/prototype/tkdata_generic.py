import target_driver
import target_io
import time
#from astropy.io import ascii
import os
import sys
import run_control
import random
import Keithley2200
import Agilent33600A
import piCom

"""
hostname = run_control.getHostName()
outdirname = run_control.getDataDirname(hostname)
runID = run_control.incrementRunNumber(outdirname)
print("Run ID: {}".format(runID))
outfile = "%srun%d.fits" % (outdirname, runID)
"""
outfile = str(raw_input("File name: ")) + ".tio"
my_ip = "192.168.12.1"
module_ip = "192.168.12.173"
initialize = True

module_def = "/Users/brent/CCC/TargetDriver/branches/issue37423/config/SCT_MSA_FPGA_Firmware0xC0000002.def"
asic_def = "/Users/brent/CCC/TargetDriver/branches/issue37423/config/TC_ASIC.def"
trigger_asic_def = "/Users/brent/CCC/TargetDriver/branches/issue37423/config/T5TEA_ASIC.def"

bps = Keithley2200.Keithley2200()
bps.powerModuleOn()
time.sleep(10)

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

#module.DisableHVAll()#disable all for safety, atm turn on by default

### Setting VPEDs ###
#with open(VPED_FILE) as f:
#  content = f.readlines()
#content = [x.strip() for x in content]
#print("Setting VPEDs to")
for asic in range(4):
  module.WriteTriggerASICSetting("VpedBias", asic, 1800, True)
  for channel in range(16):
    #print(str(asic) + "   " + str(channel) + "   " + str(asic*16+channel) + "   " + str(content[asic*16+channel]))
    module.WriteTriggerASICSetting("Vped_{}".format(channel), asic, 1200 ,True)#int(content[asic*16+channel]), True)
time.sleep(1)

### Setting optimized SSToutFB & VtrimT ###
#data = ascii.read(VTRIM_FILE)
#print(data)
for asics in range(4):
  #print("Setting SSToutFB_Delay of Asic " + str(asics) + " to " + str(int(data[asics][2])))
  module.WriteASICSetting("SSToutFB_Delay", asics, 58,True,False)#int(data[asics][2]), True, False) # standard value: 58
  #print("Setting VtrimT of Asic " + str(asics) + " to " + str(int(data[asics+4][2])))
  module.WriteASICSetting("VtrimT", asics, 1240,True,False)#int(data[asics+4][2]), True, False) # standard value: 1240
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


### let module head up a bit ###
#module.WriteSetting("ExtTriggerDirection", 0x1) # hardsync
#module.WriteSetting("TACK_EnableTrigger", 0x10000)
def take_ped():
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

    module.WriteSetting("ExtTriggerDirection", 0x1) # hardsync
    #module.WriteSetting("TACK_EnableTrigger", 0x10000)  # hardware trigger
    module.WriteSetting("TACK_EnableTrigger", 0x10000) # all channels

    for i in range(10):
	    print("\n------ Took data for {}s -------".format(i*5))
	    ret, temp =  module.GetTempI2CAux()
	    print ("Temperature Aux: ",temp)
	    time.sleep(5)

    module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers

    time.sleep(1)

    ####close connection to module and output file
    writer.StopWatchingBuffer()  # stops data storing in file

    module.CloseSockets()
    buf.Flush()
    writer.Close()

def take_sin():
    kNPacketsPerEvent = 16
    # by default we have a data packet for each channel, this can be changed
    kPacketSize = target_driver.DataPacket_CalculatePacketSizeInBytes(4, 32 * (nblocks))
    kBufferDepth = 10000

    ssh = piCom.executeConnection()
    piCom.setChannel(ssh, 1)


    fg = Agilent33600A.Agilent33600A()
    fg.apply_sin(10.0e6, 0.100, 0)

    listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
    listener.AddDAQListener(my_ip)
    listener.StartListening()
    writer = target_io.EventFileWriter(outfile, kNPacketsPerEvent, kPacketSize)
    buf = listener.GetEventBuffer()
    writer.StartWatchingBuffer(buf)

    ####start data taking

    module.WriteSetting("ExtTriggerDirection", 0x1) # hardsync
    #module.WriteSetting("TACK_EnableTrigger", 0x10000)  # hardware trigger
    module.WriteSetting("TACK_EnableTrigger", 0x10000) # all channels

    for i in range(10):
	    print("\n------ Took data for {}s -------".format(i*5))
	    ret, temp =  module.GetTempI2CAux()
	    print ("Temperature Aux: ",temp)
	    time.sleep(5)

    module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers

    time.sleep(1)
    piCom.setChannel(ssh, 0)
    fg.close()
    ####close connection to module and output file
    writer.StopWatchingBuffer()  # stops data storing in file

    module.CloseSockets()
    buf.Flush()
    writer.Close()

#take_ped()
take_sin()
bps.powerModuleOff()
