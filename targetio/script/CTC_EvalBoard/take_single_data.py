import target_driver
import target_io
import time
import os
import numpy as np
import sys


module_name = "SN0001"

#my_ip = "10.1.17.1"
my_ip = "192.168.0.2"
#module_ip = "10.1.17.17"
module_ip = "192.168.0.124"             #"192.168.0.124"  for SN0002
initialize = True

wbias = 1200
voltage_vped=700 #mV
wilkclk=0 #0=104.17, 1=156.25, 2=208.33, 3=250.00MHz
isel=2550#2550 for 104MHz, 2300 for 250MHz, 2370 for 208MHz
rampdur=5000 #5000 for 104MHz

lookup=np.loadtxt("/DATA/Messungen_Adrian/CTC_Eval_Board/CTC_and_CT5TEA/VPED/data/VPED_lookup_{}.txt".format(module_name))


module_def = "/home/cta/Software/TargetDriver/trunk/config/CTC_Eval_FPGA_Firmware0xA0000009.def"
asic_def = "/home/cta/Software/TargetDriver/trunk/config/CTC_ASIC.def"
trigger_asic_def = "/home/cta/Software/TargetDriver/trunk/config/CT5TEA_ASIC.def"






module = target_driver.TargetModule(module_def, asic_def, trigger_asic_def, 0)
if initialize:
    ret=module.EstablishSlowControlLink(my_ip, module_ip)
    print("EstablishSlowControlLink",ret,"(should be 0)")
    if ret!=0:
        print("That did not work...")
        sys.exit()
    #module.WriteSetting("PowerUpASIC0",1)
    #time.sleep(1)
    module.Initialise()
    module.EnableDLLFeedback()
    print ("module initialized")
else:
    ret=module.ReconnectToServer(my_ip, 8201, module_ip, 8105)
    print("ReconnectToServer",ret,"(should be 0)")
    if ret!=0:
        print("That did not work...")
        sys.exit()



ret, fw = module.ReadRegister(0)
print ("Firmware version: {:x}".format(fw))

ret,lsw= module.ReadSetting("SerialNumLSW")
ret,msw= module.ReadSetting("SerialNumMSW")
print("serial number: {:x} {:x}".format(msw,lsw))



time.sleep(0.1)
module.WriteSetting("T0_Select",54) 

module.WriteSetting("WilkinsonClockFreq", wilkclk)
module.WriteASICSetting("Isel", 0, isel, True)  #104MHz
#module.WriteASICSetting("Isel", 0, 2300, True)  #250MHz
module.WriteSetting("RampSignalDuration",rampdur)
module.WriteSetting("SelectSampleClockPhase", 0xF)

trigger_rate = 600

module.WriteSetting("TACK_EnableTrigger", 0x0)

#Set Modul
for asic in range(1):
    module.WriteSetting("EnableChannelsASIC{}".format(asic), 0xffff)
module.WriteSetting("Zero_Enable", 0)
module.WriteSetting("DoneSignalSpeedUp",0)

nblocks = 14
kNPacketsPerEvent = 8
module.WriteSetting("NumberOfBlocks", nblocks-1)
module.WriteSetting("MultiTrigger",9)
#mask=0b0000000000010
#module.WriteSetting("Write_Debug",0)
#time.sleep(10)

#Set Pedestral
voltage =voltage_vped


print("Set Voltage to {}".format(voltage))
for asic in range(1):
        for channel in range(16):
            vpeddac=int(lookup[channel+(asic*16),voltage])
            if vpeddac==-1:
                vpeddac=int(lookup[channel+(asic*16)+1,voltage])
            #print(vpeddac)
            module.WriteTriggerASICSetting("Vped_{}".format(channel), asic,vpeddac, True)
            print("ASIC {} Channel {} VPED {}".format(asic,channel, vpeddac))


#Set Trigger

#module.WriteSetting("TriggerDelay", 500+7+32) # lookback time between instant when the trigger is issued and the portion of the ASIC storage to digitize
#module.WriteSetting("TriggerDelay", 500-170)    # for SN0002
module.WriteSetting("TriggerDelay", 500-170)    #50    # 90 for wBaseline
module.WriteSetting("TACK_TriggerType", 0x0)
module.WriteSetting("TACK_TriggerMode", 0x0)

### let module head up a bit ###
module.WriteSetting("ExtTriggerDirection", 0x0) # 1: hardsync
module.WriteSetting("TACK_EnableTrigger", 0x0)


module.WriteSetting("MaxChannelsInPacket", int(64/kNPacketsPerEvent))

#ret, tack1 =  module.ReadSetting("CountTACKsReceived")# by default we have a data packet for each channel, this can be changed
kPacketSize = target_driver.DataPacket_CalculatePacketSizeInBytes(int(64/kNPacketsPerEvent), 32 * (nblocks))
kBufferDepth = 50000

os.system("rm delme_r0.tio")
listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
listener.AddDAQListener(my_ip)
listener.StartListening()
#writer = target_io.EventFileWriter((path_to_save + 'data_amplitude' + str(ampV)[0] +  str(ampV)[2:] + '_r0.tio'), kNPacketsPerEvent, kPacketSize)
writer = target_io.EventFileWriter('delme_r0.tio', kNPacketsPerEvent, kPacketSize)
buf = listener.GetEventBuffer()
writer.StartWatchingBuffer(buf)

####start data taking

module.WriteSetting("TACK_EnableTrigger", 0x10000)  # hardware trigger

#temperature stuff
ret,temp1 =  module.GetTempI2CEval()
if temp1 < 0:
    temp1 = -1*(temp1+128)
print ("Temperature, board: ",temp1)
try:
    while True:

        time.sleep(1)
except:
    pass

module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers


time.sleep(.1)

####close connection to module and output file
writer.StopWatchingBuffer()  # stops data storing in file
module.CloseSockets()
buf.Flush()
writer.Close()
time.sleep(.1)

#aimtti.socket_close(sock)
print("Finish, close now!")
