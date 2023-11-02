import target_driver
import target_io
import time
import os
import numpy as np
import serial
import sys
from tqdm import tqdm
sys.path.append("/home/cta/Software/Devices/GW_GPE_4323/")
import GW_GPE_4323 as gw
sys.path.append("/home/cta/Software/Devices/Siglent6052X/")
import siglent6000 as sig


def read_keysight(device,toread=21):
    device.write('READ?\r\n'.encode())
    resp=device.read(toread)
    #print("Keysight:",resp,len(resp))
    toread=len(resp)
    return(float(resp.decode()[1:toread-2]),toread)

r2temp=np.loadtxt("/DATA/Messungen_Adrian/CTC_Eval_Board/TC_and_T5TEA/ped_stability/NTC10k.txt")[:,1]


wg=sig.SDG6052X()
wg.write("C2:OUTP OFF")

multi = serial.Serial("/dev/ttyUSB1",timeout=2.)
multi.write('*IDN?\r\n'.encode())
answ0=multi.read(47)
print("Multimeter (Keysight):",answ0.decode()[:-2])

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
temp_asic = read_keysight(multi,17)
print ("Temperature initial, board: ",temp1,"ASIC:",r2temp[int(temp_asic[0])])

#module.WriteSetting("TriggerOut_Enable",0b10000000)
module.WriteASICSetting("Vdischarge",0,300,True,False)
module.WriteSetting("Hardsync_Freq", 407)
module.WriteSetting("RCLR_FINISH", 100)
module.WriteSetting("RCLR_LENGTH_END",6400)
module.WriteSetting("RampSignalDuration",1000)
time.sleep(0.2)

module.WriteSetting("TACK_EnableTrigger", 0x0)

module.WriteSetting("EnableChannelsASIC0", 0xffff)
module.WriteSetting("Zero_Enable", 1)
module.WriteSetting("DoneSignalSpeedUp",0)


module.WriteSetting("NumberOfBlocks", nblocks-1)
module.WriteSetting("SetDataPort",8107)

module.WriteSetting("TriggerDelay", 500-50+256)

### let module head up a bit ###
module.WriteSetting("ExtTriggerDirection", 0x1) # 1: hardsync


module.WriteSetting("TACK_EnableTrigger", 0x10000)
print("now sleep")
for i in tqdm(range(500)):
    time.sleep(1)

module.WriteSetting("TACK_EnableTrigger", 0x0)


module.WriteSetting("MaxChannelsInPacket", int(16/kNPacketsPerEvent))

kPacketSize = target_driver.DataPacket_CalculatePacketSizeInBytes(int(16/kNPacketsPerEvent), 32 * (nblocks))
print("Packet Size:",kPacketSize)
kBufferDepth = 10000

outpedname="/DATA/Messungen_Adrian/CTC_Eval_Board/TC_and_T5TEA/ped_stability/data/fix12_ped_restart_{}_r0.tio".format(restarts)
print("start ped {}".format(outpedname))

os.system("rm {}".format(outpedname))

#take pedestal
listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
listener.AddDAQListener(my_ip)
listener.StartListening()
writer_ped = target_io.EventFileWriter(outpedname, kNPacketsPerEvent, kPacketSize)
buf = listener.GetEventBuffer()
writer_ped.StartWatchingBuffer(buf)

#module.WriteSetting("TriggerOut_Enable",0b10000000)

#module.WriteSetting("Hardsync_Freq", 407)


ret,temp1 =  module.GetTempI2CEval()
if temp1 < 0:
    temp1 = -1*(temp1+256)
temp_asic = read_keysight(multi,17)
print ("Temperature before Ped: ",temp1,r2temp[int(temp_asic[0])])
temps_array.append([time.time(),temp1,r2temp[int(temp_asic[0])]])


phase=511-3
module.WriteSetting("TriggerDelay", 500-50+256)
module.WriteSetting("TACK_EnableTrigger", 0x10000)

print("EVEN")
for i in tqdm(range(128)):
    phase=int((phase+4)%512)
    module.WriteSetting("Hardsync_Phase",phase)
    time.sleep(0.25)

module.WriteSetting("TriggerDelay", 500-49+256)

print("ODD")

ret,temp1 =  module.GetTempI2CEval()
if temp1 < 0:
    temp1 = -1*(temp1+256)
temp_asic = read_keysight(multi,17)
print ("Temperature middle Ped: ",temp1,r2temp[int(temp_asic[0])])
temps_array.append([time.time(),temp1,r2temp[int(temp_asic[0])]])

for i in tqdm(range(128)):
    phase=int((phase+4)%512)
    module.WriteSetting("Hardsync_Phase",phase)
    time.sleep(0.25)

module.WriteSetting("TACK_EnableTrigger", 0x0)
time.sleep(.5)
writer_ped.StopWatchingBuffer()
writer_ped.Close()

buf.Clear()

wg.write("C2:OUTP ON")

phase=511-3
module.WriteSetting("Hardsync_Phase",phase)
module.WriteSetting("TriggerDelay", 500-50+256)
module.WriteSetting("ExtTriggerDirection", 0x0) #Set for external trigger

outfilename="/DATA/Messungen_Adrian/CTC_Eval_Board/TC_and_T5TEA/ped_stability/data/fix12_file_restart_{}_r0.tio".format(restarts)
print("start data {}".format(outfilename))

os.system("rm {}".format(outfilename))

writer = target_io.EventFileWriter(outfilename, kNPacketsPerEvent, kPacketSize)
writer.StartWatchingBuffer(buf)


ret,temp1 =  module.GetTempI2CEval()
if temp1 < 0:
    temp1 = -1*(temp1+256)
temp_asic = read_keysight(multi,17)
print ("Temperature before Data: ",temp1,r2temp[int(temp_asic[0])])
temps_array.append([time.time(),temp1,r2temp[int(temp_asic[0])]])

####start data taking

module.WriteSetting("TACK_EnableTrigger", 0x10000)  # hardware trigger

for i in range(20):
    ret,temp1 =  module.GetTempI2CEval()
    if temp1 < 0:
        temp1 = -1*(temp1+256)
    temp_asic = read_keysight(multi,17)
    print ("Temperature: ",temp1,r2temp[int(temp_asic[0])])
    temps_array.append([time.time(),temp1,r2temp[int(temp_asic[0])]])
    time.sleep(5)


module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers

time.sleep(.1)

####close connection to module and output file
writer.StopWatchingBuffer()  # stops data storing in file

wg.write("C2:OUTP OFF")

ret,temp1 =  module.GetTempI2CEval()
if temp1 < 0:
    temp1 = -1*(temp1+256)
temp_asic = read_keysight(multi,17)
print ("Temperature after Data: ",temp1,r2temp[int(temp_asic[0])])
temps_array.append([time.time(),temp1,r2temp[int(temp_asic[0])]])




module.CloseSockets()
buf.Flush()
writer.Close()
time.sleep(3)
command="generate_ped -i {}".format(outpedname)
os.system(command)

with open("/DATA/Messungen_Adrian/CTC_Eval_Board/TC_and_T5TEA/ped_stability/data/temperatures_pedtest_fix12.txt", "a") as f:
    np.savetxt(f,temps_array)

print("Finish, close now!")
exit(0)
