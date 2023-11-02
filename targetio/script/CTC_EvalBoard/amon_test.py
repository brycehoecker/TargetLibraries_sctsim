import target_driver
import target_io
import time
import os
import numpy as np
import sys
sys.path.append("/home/cta/Software/Devices/Fluke_8808a")
import fluke8808A as fl
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.use('TkAgg')


group=[16,16,16,16,0,1,2,3]

inst=fl.F8808A()
inst.set_readvolt()

module_name = "SN0001"

#my_ip = "10.1.17.1"
my_ip = "192.168.0.2"
#module_ip = "10.1.17.17"
module_ip = "192.168.0.125"             #"192.168.0.124"  for SN0002
initialize = False

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
voltage = voltage_vped

print("Set Voltage to {}".format(voltage))
for asic in range(1):
        for channel in range(16):
            vpeddac=int(lookup[channel+(asic*16),voltage])
            #vpeddac=1200
            if vpeddac==-1:
                vpeddac=int(lookup[channel+(asic*16)+1,voltage])
            #print(vpeddac)
            module.WriteTriggerASICSetting("Vped_{}".format(channel), asic,vpeddac, True)
            print("ASIC {} Channel {} VPED {}".format(asic,channel, vpeddac))


voltage = 700
#for asic in range(1):
#        for channel in range(4):
#            vpeddac=int(lookup[channel+(asic*16),voltage])
#            if vpeddac==-1:
#                vpeddac=int(lookup[channel+(asic*16)+1,voltage])
#            #print(vpeddac)
#            module.WriteTriggerASICSetting("Vped_{}".format(channel), asic,vpeddac, True)
#            print("ASIC {} Channel {} VPED {}".format(asic,channel, vpeddac))



module.WriteTriggerASICSetting("TTbias_A",0,1800,True)
module.WriteTriggerASICSetting("AmonSelect",0,4,True)

module.WriteTriggerASICSetting("TRGsumbias",0,1200,True)

results=[]
vals=[0,0,0,0,0,0,0,0]

#for m in range(0,4000,1000):
#    for l in range(0,4000,1000):
#        for k in range(0,4000,1000):
#            for j in range(0,4000,1000):
#                for i in range(0,4000,1000):
i=1865
j=1865
k=1865
l=1865
m=1800

#for i in range(500,3601,200):
#    for j in range(1500,2501,250):
#        for k in range(1500,2501,250):
#            for l in range(1500,2501,250):
for t in range(1):

    #i=ii
    #j=ii
    #k=ii
    #l=ii

    module.WriteTriggerASICSetting("PMTref4_0",0,i,True)
    module.WriteTriggerASICSetting("PMTref4_1",0,j,True)
    module.WriteTriggerASICSetting("PMTref4_2",0,k,True)
    module.WriteTriggerASICSetting("PMTref4_3",0,l,True)
    module.WriteTriggerASICSetting("PMTref4_sum",0,m,True)
    print("PMTref",i,j,k,l,m)
    for n in range(3,8):
        module.WriteTriggerASICSetting("AmonSelect",0,n,True)
        #module.WriteTARGETRegister(True,False,False,False,True,True,0x36,2**n,True)
        time.sleep(.2)
        if n==4 or i ==3:
            time.sleep(.2)
        #print(n,inst.read_value())
        vals[n]=(inst.read_value())
        print("group",group[n],vals[n],"V")
    results.append([i,j,k,l,m,vals[3],vals[4],vals[5],vals[6],vals[7]])
results=np.array(results)

module.CloseSocket()

xx=0
plt.plot(results[:,xx],1000.*results[:,5],label='sum')
plt.plot(results[:,xx],1000.*results[:,6],label='1')
plt.plot(results[:,xx],1000.*results[:,7],label='2')
plt.plot(results[:,xx],1000.*results[:,8],label='3')
plt.plot(results[:,xx],1000.*results[:,9],label='4')

plt.xlabel("PMTref4_sum [ADC counts]")
plt.ylabel("Amon [mV]")
plt.legend()
plt.tight_layout()
plt.show()

#print(results)
#np.savetxt("data.txt",results)
