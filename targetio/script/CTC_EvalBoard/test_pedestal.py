import target_driver
import target_io
import time
import os
import numpy as np
import serial
import sys
sys.path.append("/home/cta/Software/Devices/GW_GPE_4323/")

import GW_GPE_4323 as gw

psu=gw.GPE_4323(49)
my_ip = "192.168.0.1"
module_ip = "192.168.0.123"
initialize = True

restarts = int(sys.argv[1])

module_def = "/home/cta/Software/TargetDriver/trunk/config/CTC_Eval_FPGA_Firmware0xA0000002.def"

asic_def = "/home/cta/Software/TargetDriver/trunk/config/TC_ASIC.def"
trigger_asic_def = "/home/cta/Software/TargetDriver/trunk/config/CT5TEA_ASIC.def"



nblocks = 4
kNPacketsPerEvent = 1

temps_array=[]


psu.switch_off()
time.sleep(3)
psu.switch_on()
time.sleep(5)

if initialize:
    module = target_driver.TargetModule(module_def, asic_def, trigger_asic_def, 0)
    module.EstablishSlowControlLink(my_ip, module_ip)
    module.Initialise()
    module.EnableDLLFeedback()
    print ("module initialized")
else:
    module.ReconnectToServer(my_ip, 8201, module_ip, 8105)

#wg=sig.SDG6052X()
#wg.write("C1:OUTP OFF")

#split=ss.Splitter(4)
#split.enableChannels(0)

ret, fw = module.ReadRegister(0)
print ("Firmware version: {:x}".format(fw))
if fw != 0xa0000002:
    print("not really connected try again")
    exit(-1)

lookup=np.loadtxt("/DATA/Messungen_Adrian/CTC_Eval_Board/TC_and_T5TEA/VPED/data/VPED_lookup.txt")

voltage=800
for channel in range(0,16):
    vpeddac=int(lookup[channel,voltage])
    module.WriteTriggerASICSetting("Vped_{}".format(channel),0,vpeddac,True)
    print("Set Channel {} to VPED {}".format(channel,vpeddac))

ret,temp1 =  module.GetTempI2CEval()
if temp1 < 0:
    temp1 = -1*(temp1+128)
print ("Temperature initial: ",temp1)

#module.WriteSetting("TriggerOut_Enable",0b10000000)
module.WriteASICSetting("Vdischarge",0,300,True,False)
module.WriteSetting("Hardsync_Freq", 0xEFFF)
module.WriteSetting("RCLR_FINISH", 1000)

time.sleep(0.2)

module.WriteSetting("TACK_EnableTrigger", 0x0)

module.WriteSetting("EnableChannelsASIC0", 0xffff)
module.WriteSetting("Zero_Enable", 1)
module.WriteSetting("DoneSignalSpeedUp",0)


module.WriteSetting("NumberOfBlocks", nblocks-1)
module.WriteSetting("SetDataPort",8107)

module.WriteSetting("TriggerDelay", 500-50)

### let module head up a bit ###
module.WriteSetting("ExtTriggerDirection", 0x1) # 1: hardsync


module.WriteSetting("TACK_EnableTrigger", 0x10000)
time.sleep(120)
module.WriteSetting("TACK_EnableTrigger", 0x0)


module.WriteSetting("MaxChannelsInPacket", int(16/kNPacketsPerEvent))

kPacketSize = target_driver.DataPacket_CalculatePacketSizeInBytes(int(16/kNPacketsPerEvent), 32 * (nblocks))
print("Packet Size:",kPacketSize)
kBufferDepth = 10000
outfilename="data/fix8_file_restart_{}_r0.tio".format(restarts)
print("start data {}".format(outfilename))

os.system("rm {}".format(outfilename))

listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
listener.AddDAQListener(my_ip)
listener.StartListening()
writer = target_io.EventFileWriter(outfilename, kNPacketsPerEvent, kPacketSize)
buf = listener.GetEventBuffer()
writer.StartWatchingBuffer(buf)



ret,temp1 =  module.GetTempI2CEval()
if temp1 < 0:
    temp1 = -1*(temp1+256)
print ("Temperature before Data: ",temp1)
temps_array.append([time.time(),temp1])


####start data taking


module.WriteSetting("TACK_EnableTrigger", 0x10000)  # hardware trigger

for i in range(100):
    ret,temp1 =  module.GetTempI2CEval()
    print ("Temperature: ",temp1)
    temps_array.append([time.time(),temp1])
    time.sleep(5)


module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers

time.sleep(.1)

####close connection to module and output file
writer.StopWatchingBuffer()  # stops data storing in file

ret,temp1 =  module.GetTempI2CEval()
if temp1 < 0:
    temp1 = -1*(temp1+256)
print ("Temperature after Data: ",temp1)
temps_array.append([time.time(),temp1])




module.CloseSockets()
buf.Flush()
writer.Close()
time.sleep(3)
command="generate_ped -i {}".format(outfilename)
os.system(command)

with open("data/temperatures_pedtest_fix8.txt", "a") as f:
    np.savetxt(f,temps_array)

print("Finish, close now!")
exit(0)
