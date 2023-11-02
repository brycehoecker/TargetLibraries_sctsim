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

my_ip = "192.168.0.2"
module_ip = "192.168.0.125"
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
lookup=np.loadtxt("/DATA/Messungen_Adrian/CTC_Eval_Board/CTC_and_CT5TEA/VPED/data/VPED_lookup_SN0001.txt")

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
print ("firmware version: {:x}".format(fw))

ret,lsw= module.ReadSetting("SerialNumLSW")
ret,msw= module.ReadSetting("SerialNumMSW")
print("serial number: {:x} {:x}".format(msw,lsw))

#exit()

if fw==0:
    sys.exit()
if initialize:
    time.sleep(1)

for j in range(16):
     vpeddac=int(lookup[j,voltage_vped])
     print("Channel",j,"VPED DAC",vpeddac)
     module.WriteTriggerASICSetting("Vped_{}".format(j),0,vpeddac,True)

time.sleep(0.1)

module.WriteSetting("ExtTriggerDirection", 0x0)
module.WriteSetting("TACK_EnableTrigger", 0x0)

module.WriteSetting("T0_Select",79)  #76 = TRIG0
module.WriteSetting("T1_Select",0)  #76 = TRIG0
module.WriteSetting("TriggerOut_Enable",1)

module.WriteTriggerASICSetting("PMTref4_0",0,2200)
module.WriteTriggerASICSetting("Thresh_0",0,2000)
module.WriteTriggerASICSetting("PMTref4_1",0,2200)
module.WriteTriggerASICSetting("Thresh_1",0,2000)
module.WriteTriggerASICSetting("PMTref4_2",0,2200)
module.WriteTriggerASICSetting("Thresh_2",0,2000)
module.WriteTriggerASICSetting("PMTref4_3",0,2200)
module.WriteTriggerASICSetting("Thresh_3",0,2000)

#for i in range(128):
    #module.WriteSetting("T1_Select",i)
    #print(i)
    #time.sleep(.5)



#module.WriteTriggerASICSetting("PMTref4_1",0,2000)
#module.WriteTriggerASICSetting("Thresh_1",0,2500)

#module.WriteTriggerASICSetting("PMTref4_2",0,2000)
#module.WriteTriggerASICSetting("Thresh_2",0,2500)

#module.WriteTriggerASICSetting("PMTref4_3",0,2000)
#module.WriteTriggerASICSetting("Thresh_3",0,2500)
#for i in range(1000,3000,100):
    #print("Threshold",i)
    #module.WriteTriggerASICSetting("Thresh_0",0,i)
    #time.sleep(0.2)

#module.WriteSetting("TriggerEff_Enable",1)
#for i in range(1000,3000,20):
#    module.WriteTriggerASICSetting("PMTref4_0",0,i)
#    rate=(Efficiency(0.1))-1
#    print("PMTref4",i,"Rate",rate/.1)

#module.WriteSetting("TriggerEff_Enable",0)
print("Finish, close now!")
module.CloseSockets()
