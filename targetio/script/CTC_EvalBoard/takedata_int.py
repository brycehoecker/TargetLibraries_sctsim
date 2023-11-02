import target_driver
import target_io
import time
import os
import numpy as np
import serial
import sys
sys.path.append("/home/cta/Software/Devices/Siglent6052X/")
import siglent6000 as sig
sys.path.append("/home/cta/Software/Devices/Splitter/")
import single_splitter as ss
pulsefreq=10000.
triggertime=0.1


def Efficiency(trig_eff_duration):
    module.WriteSetting("TriggerEff_Duration", int(trig_eff_duration*125000000))
    ret, done_bit = module.ReadSetting("TriggerEff_DoneBit")
    time.sleep(0.1)
    while done_bit == 0:
        ret, done_bit = module.ReadSetting("TriggerEff_DoneBit")
    ret, N = module.ReadSetting("TriggEffCounter")
    return N

my_ip = "192.168.0.1"
module_ip = "192.168.0.123"
initialize = True


module_def = "/home/cta/Software/TargetDriver/trunk/config/CTC_Eval_FPGA_Firmware0xA0000002.def"

asic_def = "/home/cta/Software/TargetDriver/trunk/config/TC_ASIC.def"
trigger_asic_def = "/home/cta/Software/TargetDriver/trunk/config/CT5TEA_ASIC.def"

module = target_driver.TargetModule(module_def, asic_def, trigger_asic_def, 0)
if initialize:
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

#module.WriteSetting("T0_Select",57)

#module.WriteSetting("Hardsync_Phase", 50)

#
module.WriteSetting("Hardsync_Freq", 0x8FFF)

#exit()

#sock = aimtti.socket_connect()
#waveform = aimtti.read_out_waveform("/home/cta/Desktop/data_shaper.txt",0)

#aimtti.socket_write(sock,"CHN 1\n")
#sock = aimtti.socket_connect()
#answer=aimtti.socket_query(sock,"CHN?")
#ampV=0.10
#aimtti.send_wave_data(sock,waveform,ampV,10000.)   #Read in Pulse
#aimtti.socket_close(sock)

#Couple the Triggersignal infront of the Pulse
#aimtti.socket_write(sock,"CHN 2\n")
#aimtti.socket_write(sock, "CHN2CONFIG SYNCOUT\n")
#aimtti.socket_write(sock, "CHN2CONFIG MAINOUT\n")
#Give the Pulsegenerator some time to change
time.sleep(0.2)

module.WriteSetting("TACK_EnableTrigger", 0x0)


module.WriteSetting("EnableChannelsASIC0", 0xffff)
module.WriteSetting("Zero_Enable", 1)
module.WriteSetting("DoneSignalSpeedUp",0)

nblocks = 4
kNPacketsPerEvent = 1
module.WriteSetting("NumberOfBlocks", nblocks-1)
module.WriteSetting("SetDataPort",8107)

module.WriteSetting("TriggerDelay", 500-58)




#0x7D0
#module.WriteSetting("RampSignalDuration",2099)

module.WriteSetting("RCLR_FINISH",1000)
#
module.WriteSetting("TriggerOut_Enable",0b10000000)
module.WriteSetting("T0_Select",35)
module.WriteSetting("T1_Select",8)
module.WriteSetting("T2_Select",9)
module.WriteSetting("T3_Select",10)





while True:
    module.DisableDLLFeedBack()
    module.StopSampling()

    time.sleep(0.1)
    module.EnableDLLFeedback()

    ### let module head up a bit ###
    module.WriteSetting("ExtTriggerDirection", 0x1) # 1: hardsync

    module.WriteSetting("Hardsync_Freq", 0x1FF)

    module.WriteSetting("TACK_EnableTrigger", 0x10000)
    name = input("Continue?")



exit()

#time.sleep(120)
module.WriteSetting("TACK_EnableTrigger", 0x0)
module.WriteSetting("MaxChannelsInPacket", int(16/kNPacketsPerEvent))


kPacketSize = target_driver.DataPacket_CalculatePacketSizeInBytes(int(16/kNPacketsPerEvent), 32 * (nblocks))
print("Packet Size:",kPacketSize)
kBufferDepth = 10000




#ret, tack1 =  module.ReadSetting("CountTACKsReceived")# by default we have a data packet for each channel, this can be changed


module.WriteSetting("TACK_EnableTrigger", 0x10000)
time.sleep(15)
module.WriteSetting("TACK_EnableTrigger", 0x0)

module.WriteSetting("Hardsync_Freq", 0x1FF)

os.system("rm delme_r0.tio")

print("start data")

listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
listener.AddDAQListener(my_ip)
listener.StartListening()
writer = target_io.EventFileWriter('delme_r0.tio', kNPacketsPerEvent, kPacketSize)
buf = listener.GetEventBuffer()
writer.StartWatchingBuffer(buf)

temps_array=[]

ret,temp1 =  module.GetTempI2CEval()
if temp1 < 0:
    temp1 = -1*(temp1+256)
print ("Temperature before Data: ",temp1)
temps_array.append([time.time(),temp1])


####start data taking


module.WriteSetting("TACK_EnableTrigger", 0x10000)  # hardware trigger

try:
    while True:
        ret,temp1 =  module.GetTempI2CEval()
        print ("Temperature: ",temp1)
        temps_array.append([time.time(),temp1])
        time.sleep(5)
except:
    pass


module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers

time.sleep(.1)

####close connection to module and output file
writer.StopWatchingBuffer()  # stops data storing in file

ret,temp1 =  module.GetTempI2CEval()
if temp1 < 0:
    temp1 = -1*(temp1+256)
print ("Temperature after Data: ",temp1)
temps_array.append([time.time(),temp1])


np.savetxt('temperatures.txt',temps_array)

module.CloseSockets()
buf.Flush()
writer.Close()

print("Finish, close now!")
