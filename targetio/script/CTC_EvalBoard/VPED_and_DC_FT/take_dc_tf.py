import target_driver
import target_io
import time
import os
import numpy as np
import sys
from tqdm import tqdm

pulsgen = "AIM"
#pulsgen="NONE"

if pulsgen == "AIM":
    import aimtti_TGF3000 as aim
if pulsgen == "SIG":
    sys.path.append("/home/cta/Software/Devices/Siglent6052X/")
    import siglent6000 as sig


def print_temp(module) :
    ret,temp1 =  module.GetTempI2CEval()
    if temp1 < 0:
        temp1 = -1*(temp1+128)
    return temp1

path="/DATA/Messungen_Adrian/CTC_Eval_Board/CTC_and_CT5TEA/DC_TF"
#path="/home/cta"

if pulsgen == "AIM":
    aimtti=aim.TGF3000()
    aimtti.tgf_output(1,"OFF")
    aimtti.tgf_output(2,"OFF")
    aimtti.write("WAVE PULSE")
    aimtti.write("CHN 2")
    aimtti.write("PULSFREQ  2000")
    aimtti.write("PULSWID 25e-9")
    aimtti.write("PULSEDGE 10e-9")
    aimtti.write("HILVL 2.5")
    aimtti.write("LOLVL 0")
#aimtti.socket_write(instr,"OUTPUT OFF\n")
#aimtti.socket_write(instr,"WAVE SINE\n")
#
#aimtti.socket_write(instr,"AMPL 2.0\n")
#aimtti.socket_write(instr,"ZLOAD 50\n")

if pulsgen == "SIG":
    instr=sig.SDG6052X()
    instr.write('*RST')
    time.sleep(.5)
    instr.write('C1:OUTP OFF')
    instr.write('C1:OUTP LOAD,50')
    instr.write('C2:OUTP OFF')
    instr.write('C2:OUTP LOAD,50')
    instr.write('C2:BSWV WVTP,PULSE')
    instr.write('C2:BSWV FRQ,2000')
    instr.write('C2:BSWV WIDTH,50e-9')
    instr.write('C2:BSWV RISE,20e-9')
    instr.write('C2:BSWV FALL,20e-9')
    instr.write('C2:BSWV HLEV,2.5')
    instr.write('C2:BSWV LLEV,0')


my_ip = "192.168.0.2"
module_ip = "192.168.0.124"
initialize = True
sampleclockphase = 1
basename = "SN002_208MHz_amplitude"


module_def = "/home/cta/Software/TargetDriver/trunk/config/CTC_Eval_FPGA_Firmware0xA0000009.def"

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


ret, fw = module.ReadRegister(0)
if fw == 0:
    sys.exit()
print ("Firmware version: 0x{:x}".format(fw))

lookup=np.loadtxt("../VPED/data/VPED_lookup_SN0002.txt")

module.WriteSetting("TACK_EnableTrigger", 0x0)

module.WriteSetting("EnableChannelsASIC0", 0xffff)
module.WriteSetting("Zero_Enable", 1)
module.WriteSetting("DoneSignalSpeedUp",0)

module.WriteSetting("WilkinsonClockFreq", 2)
module.WriteASICSetting("Isel", 0, 2370, True)
module.WriteSetting("RampSignalDuration",2100)
if sampleclockphase==1:
    module.WriteSetting("SelectSampleClockPhase", 0xF)
else:
    module.WriteSetting("SelectSampleClockPhase", 0x0)

nblocks = 4
kNPacketsPerEvent = 1
module.WriteSetting("NumberOfBlocks", nblocks-1)

vped = 1200
print("Setting VPEDs to",vped)
for channel in range(16):
    module.WriteTriggerASICSetting("Vped_{}".format(channel), 0, vped, True)

module.WriteSetting("SetDataPort",8107)
module.WriteSetting("TriggerDelay", 450-80)
module.WriteSetting("TACK_TriggerType", 0x0)
module.WriteSetting("TACK_TriggerMode", 0x0)



module.WriteSetting("MaxChannelsInPacket", int(16/kNPacketsPerEvent))

#ret, tack1 =  module.ReadSetting("CountTACKsReceived")# by default we have a data packet for each channel, this can be changed
kPacketSize = target_driver.DataPacket_CalculatePacketSizeInBytes(int(16/kNPacketsPerEvent), 32 * (nblocks))
kBufferDepth = 20000


voltvals=[]
i=0
to_append=True
while i < 2300:
     voltage=i
     DAC=lookup[:,voltage]
     while np.count_nonzero(DAC==-1)>0:
         voltage+=1
         if voltage>=2500:
             to_append=False
             break
         DAC=lookup[:,voltage]
     if to_append:
         voltvals.append(voltage)
     i=(voltage+50)-(voltage+50)%50

#generate the config for TargetCalib
file = open("data/config_2.txt","w")
for i in voltvals:
    file.write("{}/data/{}_{}_r0.tio {}\n".format(path,basename,i,i))
file.close()

print("Will use {} voltage values: {}".format(len(voltvals),voltvals))

module.WriteSetting("ExtTriggerDirection", 0x0) # 1: hardsync
module.WriteSetting("TACK_EnableTrigger", 0x10000)

if pulsgen == "AIM":
    aimtti.tgf_output(2,"ON")
if pulsgen == "SIG":
    instr.write('C2:OUTP ON')

print("waiting to warm up")
if initialize:
    for i in tqdm(range(300)):
        time.sleep(1)
else:
    for i in tqdm(range(10)):
        time.sleep(1)

if pulsgen == "AIM":
    aimtti.tgf_output(2,"OFF")
if pulsgen == "SIG":
    instr.write('C2:OUTP OFF')

module.WriteSetting("TACK_EnableTrigger", 0)


print("start data")


listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
listener.AddDAQListener(my_ip)
listener.StartListening()




buf = listener.GetEventBuffer()

for voltage in voltvals:
    try_again=True
    while(try_again):
        module.WriteSetting("TACK_EnableTrigger", 0)
        print("\nSet Voltage to {}".format(voltage))
        try:
            if  os.stat("data/{}_{}_r0.tio".format(basename,voltage)).st_size<666666666:
                print("File exists but to small ({}MB) do again".format((os.stat("data/{}_{}_r0.tio".format(basename,voltage)).st_size)/1000000))
                os.remove("data/{}_{}_r0.tio".format(basename,voltage))
        except:
            pass
        if  os.path.isfile("data/{}_{}_r0.tio".format(basename,voltage)):
            print("File already exsits")
            break
        for channel in range(16):
            vpeddac=int(lookup[channel,voltage])
            #print(vpeddac)
            module.WriteTriggerASICSetting("Vped_{}".format(channel),0,vpeddac,True)

        writer = target_io.EventFileWriter('data/{}_{}_r0.tio'.format(basename,voltage), kNPacketsPerEvent, kPacketSize)
        writer.StartWatchingBuffer(buf)

    ####start data taking

        print ("Temperature: ", print_temp(module))

        module.WriteSetting("TACK_EnableTrigger", 0x10000)  # hardware trigger
        if pulsgen == "AIM":
            aimtti.tgf_output(2,"ON")
        if pulsgen == "SIG":
            instr.write('C2:OUTP ON')
        sleeptime=10.
        for i in range (8):
            ret, precount = module.ReadSetting("CountTACKsReceived")
            time.sleep(sleeptime)
            ret, postcount = module.ReadSetting("CountTACKsReceived")
            print("Software received",int(buf.GetEventRate()),"Target Module send",(postcount-precount)/sleeptime)

        if pulsgen == "AIM":
            aimtti.tgf_output(2,"OFF")
        if pulsgen == "SIG":
            instr.write('C2:OUTP OFF')


        time.sleep(0.1)
        ret = 1
        while ret != 0:
            ret =  module.WriteSetting("TACK_EnableTrigger", 0)
        time.sleep(0.1)
        writer.StopWatchingBuffer()  # stops data storing in file
        writer.Close()
        buf.Clear()
        buf.Flush()
        if  os.stat("data/{}_{}_r0.tio".format(basename,voltage)).st_size<666666666:
            print("Something went wrong, only {}MB do again".format((os.stat("data/{}_{}_r0.tio".format(basename,voltage)).st_size)/1000000))
            os.remove("data/{}_{}_r0.tio".format(basename,voltage))
            try_again=True
        else:
            try_again=False


module.CloseSockets()

writer.Close()


print("Finish, close now!")

#exit()

module.CloseSockets()
