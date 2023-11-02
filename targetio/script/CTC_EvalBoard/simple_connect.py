import sys
sys.path.append("/home/cta/anaconda3/envs/cta/lib/python3.8/site-packages")
import target_driver
import target_io
import time
import os
import numpy as np
import serial
import aimtti_TGF3000 as aimtti


def Efficiency(trig_eff_duration):
    module.WriteSetting("TriggerEff_Duration", int(trig_eff_duration*125000000))
    ret, done_bit = module.ReadSetting("TriggerEff_DoneBit")
    time.sleep(0.1)
    while done_bit == 0:
        ret, done_bit = module.ReadSetting("TriggerEff_DoneBit")
    ret, N = module.ReadSetting("TriggEffCounter")
    return N

#my_ip = "10.1.17.1"
my_ip = "192.168.0.2"
#module_ip = "10.1.17.17"
module_ip = "192.168.0.124"
if len(sys.argv)>1:
    if sys.argv[1] == "False":
        initialize = False
    elif sys.argv[1] == "True":
        initialize = True
    else:
        print(sys.argv[1],"is not True or False")
else:
    initialize = False
if len(sys.argv)>2:
    voltage_vped=int(sys.argv[2])
    print("Set VPED to {}mV".format(voltage_vped))
else:
    voltage_vped=800 #mV

#initialize = True
wbias = 1200
ctc_vbias = 1200  #1200 default
vpedbias = 1800  #1800 default
wilkclk=3 #0=104.17, 1=156.25, 2=208.33, 3=250.00MHz
isel=2370#2550 for 104MHz, 2300 for 250MHz, 2370 for 208MHz
rampdur=2500 #5000 for 104MHz
lookup=np.loadtxt("/DATA/Messungen_Adrian/CTC_Eval_Board/CTC_and_CT5TEA/VPED/data/VPED_lookup_SN0002.txt")
#lookup=np.loadtxt("SN0037_VPED_lookup.txt")


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
#module.StopSampling()
#module.ModifyModuleIP(123)


ret, fw = module.ReadRegister(0)
print ("firmware version: {:x}".format(fw))

ret,lsw= module.ReadSetting("SerialNumLSW")
ret,msw= module.ReadSetting("SerialNumMSW")
print("serial number: {:x} {:x}".format(msw,lsw))

#exit()

if fw==0:
    sys.exit()
if initialize:
    time.sleep(1)
# Set correct dac counts for vped to get required voltage
for j in range(16):
     vpeddac=int(lookup[j,voltage_vped])
     print("Channel",j,"VPED DAC",vpeddac)
     module.WriteTriggerASICSetting("Vped_{}".format(j),0,vpeddac,True)
     #time.sleep(0.1)

module.WriteASICSetting("Vbias", 0, ctc_vbias)
module.WriteTriggerASICSetting("VpedBias", 0, vpedbias)
#exit()
#module.WriteTriggerASICSetting("Wbias_0",0,wbias,True)
#module.WriteTriggerASICSetting("PMTref4_0", 0, 2140, True)
#module.WriteTriggerASICSetting("Thresh_0", 0,2000, True)

#i=50
#while True:
#    print(i)
#module.WriteSetting("T1_Select",76)
#    i=i+1
#    if i>100:
#        i=50
#    time.sleep(1)

#sys.exit()
module.WriteSetting("Storage_Sel",0)
module.WriteSetting("TriggerDelay", 0)#450-80)
module.WriteSetting("MultiTrigger",0)

#module.WriteSetting("Hardsync_Freq",0x8FFF)
module.WriteSetting("TriggerOut_Enable",0b10000000)
#module.WriteSetting("T0_Select",70)
#module.WriteASICSetting("Vbias", 0, ctc_vbias)
#module.WriteTriggerASICSetting("Vbias", 0, ct5tea_vbias)

module.WriteASICSetting("WR_ADDR_Incr1LE_Delay", 0, (55+0)%64)
module.WriteASICSetting("WR_ADDR_Incr1TE_Delay", 0,  (6+0)%64)
module.WriteASICSetting("WR_STRB1LE_Delay",      0, (25-0)%64)
module.WriteASICSetting("WR_STRB1TE_Delay", 0, (25 + 10-0)%64)
module.WriteASICSetting("WR_ADDR_Incr2LE_Delay", 0, (55+0)%64)
module.WriteASICSetting("WR_ADDR_Incr2TE_Delay", 0,  (6+0)%64)
module.WriteASICSetting("WR_STRB2LE_Delay",      0, (61-0)%64)
module.WriteASICSetting("WR_STRB2TE_Delay",      0,  (7-0)%64)


#exit()
#module.StopSampling()

time.sleep(0.1)
#module.EnableDLLFeedback()
#module.StartSampling()

module.WriteSetting("WilkinsonClockFreq", wilkclk)
module.WriteASICSetting("Isel", 0, isel, True)  #104MHz
#module.WriteASICSetting("Isel", 0, 2300, True)  #250MHz
module.WriteSetting("RampSignalDuration",rampdur)
module.WriteSetting("SelectSampleClockPhase", 0xF)

#module.WriteASICSetting("Vdischarge", 0, 0, True)

#module.WriteASICSetting("Vbias",0,1200,True)

module.WriteSetting("ExtTriggerDirection", 0x1)
#module.WriteSetting("TACK_EnableTrigger", 0x10000)
#exit()
#i=8


# vped=2095
# for channel in range(16):
#      module.WriteTriggerASICSetting("Vped_{}".format(channel), 0, vped, True)


#for i in range(64):
##    print(i)

# module.WriteSetting("T1_Select",0)

# module.WriteSetting("T2_Select",54)
# module.WriteSetting("T3_Select",0)
#
#module.WriteSetting("Hardsync_Freq",0x1500)

module.WriteTARGETRegister(True,False,False,False,True,True,0x5b,0)

module.WriteSetting("Write_Debug",0b0)

time.sleep(0.2)

module.WriteSetting("TACK_EnableTrigger", 0x0)

for asic in range(1):
    module.WriteSetting("EnableChannelsASIC{}".format(asic), 0xffff)
module.WriteSetting("Zero_Enable", 0)
module.WriteSetting("DoneSignalSpeedUp",0)

nblocks = 4
kNPacketsPerEvent = 2
module.WriteSetting("NumberOfBlocks", nblocks-1)


module.WriteSetting("TACK_TriggerType", 0x0)
module.WriteSetting("TACK_TriggerMode", 0x0)

#module.WriteSetting("DurationofDeadtime",25000)
#module.WriteSetting("DurationofDeadtime",1000)
#module.WriteSetting("SR_DisableTrigger", 1)
#module.WriteSetting("RCLR_LENGTH_END",10) #in 10us steps

### let module head up a bit ###
#module.WriteSetting("ExtTriggerDirection", 0x0) # 1: hardsync
#module.WriteSetting("TACK_EnableTrigger", 0x0)




module.WriteSetting("MaxChannelsInPacket", int(64/kNPacketsPerEvent))

#ret, tack1 =  module.ReadSetting("CountTACKsReceived")# by default we have a data packet for each channel, this can be changed
kPacketSize = target_driver.DataPacket_CalculatePacketSizeInBytes(int(64/kNPacketsPerEvent), 32 * (nblocks))
kBufferDepth = 10000

#exit()

print("start data")


os.system("rm delme_r0.tio")

#module.WriteSetting("TriggerEff_Enable", 2**0)
#module.WriteSetting("CoincidenceEnable",0)

#print("Measure?",Efficiency(1))
listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
listener.AddDAQListener(my_ip)
listener.StartListening()
writer = target_io.EventFileWriter('delme_r0.tio', kNPacketsPerEvent, kPacketSize)
buf = listener.GetEventBuffer()
writer.StartWatchingBuffer(buf)

####start data taking

module.WriteSetting("TACK_EnableTrigger", 0x10000)  # hardware trigger
sleeptime=5.
delay=0
rounds=0
try:
    while(rounds<40):
        ret, precount = module.ReadSetting("CountTACKsReceived")
        #for i in range(sleeptime):
        #    module.WriteSetting("TriggerDelay", delay)
        #    delay=(delay-100)%16384
        time.sleep(sleeptime)
        ret, postcount = module.ReadSetting("CountTACKsReceived")
        if postcount<precount:
            postcount=postcount+65536
        print("Software received",int(buf.GetEventRate()),"Target Module send",(postcount-precount)/sleeptime)
        buf.GetEventRate()
        rounds+=1
        #break

except:
    pass

module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers

time.sleep(.5)

####close connection to module and output file
writer.StopWatchingBuffer()  # stops data storing in file
#ret, tack2 =  module.ReadSetting("CountTACKsReceived")
#print ("\nReiceved",tack2-tack1,"triggers\n\n",tack1,'\n',tack2,'\n\n')
module.CloseSockets()
buf.Flush()
writer.Close()

print("Finish, close now!")


module.CloseSockets()
