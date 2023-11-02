#First argument is SN, second channel range (0-31 or 32-63)

import target_driver
import target_io
import time
import os
import datetime
import sys
import numpy as np
sys.path.append("/home/cta/Software/Devices/Fluke_8846A/")
import fluke_8846a as fl



def print_temp(module) :
    ret,temp1 =  module.GetTempI2CEval()
    if temp1 < 0:
        temp1 = -1*(temp1+128)
    return temp1

if len(sys.argv)>1:
    channel = sys.argv[1]
else:
    channel = 99

print("Will take VPED for channel",channel)
trycounter=0
while True:
    if trycounter>10:
        print("Can't connect to Fluke")
        sys.exit()
    try:
        multi=fl.F8846A()
        break
    except:
        time.sleep(1)
        trycounter+=1
multi.set_read()




my_ip = "192.168.0.2"
module_ip = "192.168.0.125"
initialize = True

module_def = "/home/cta/Software/TargetDriver/trunk/config/CTC_Eval_FPGA_Firmware0xA0000009.def"

asic_def = "/home/cta/Software/TargetDriver/trunk/config/CTC_ASIC.def"
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
    exit()
#module.ModifyModuleIP(125)
#exit()
print("Firmware version: 0x{:x}".format(fw))
print("Test channels")
for i in range(0,16):
    module.WriteTriggerASICSetting("Vped_{}".format(i), 0, 0, True)
for i in range(0,16):
    module.WriteTriggerASICSetting("Vped_{}".format(i), 0, 4000, True)
    #read=multi.read_value()*1000.
    #print(read)
    #time.sleep(0.15)
    read=multi.read_value()*1000.
    readvolts=np.mean(np.array(read))
    print("Channel {}, Voltage {:.2f} mV".format(i,readvolts))
    time.sleep(0.05)
    module.WriteTriggerASICSetting("Vped_{}".format(i), 0, 0, True)
    #print(channel,i,readvolts)
    if (readvolts>1500 and i!=int(channel)):
        print("Channel {} connected instead of {}".format(i,channel))
        sys.exit()
    if (readvolts<1500 and i==int(channel)):
        print("Channel {} not connected".format(channel))
        sys.exit()


module.WriteTriggerASICSetting("Vped_{}".format(channel), 0, 4000, True)




#time.sleep(5)

tf_filename = "data/VPED_TF_{}.txt".format(channel)

try:
    os.system("mv {} data/old_vped_tf_file_{}.txt".format(tf_filename,channel))
except:
    pass

tf_file = open(tf_filename,"w")

vpedlist=[]

# 512 schritte im 16er Abstand
#for i in range(1,513):
#    if i % 2 :
#        vpedlist.append(int(i/2)*16)
#    else :
#        vpedlist.append(int(i/2)*16-1)

for i in range(0,4096):
    vpedlist.append(i)

for vped in vpedlist:
    #print(type(vped))
    temps=print_temp(module)
    for j in range(16):
        module.WriteTriggerASICSetting("Vped_{}".format(j), 0, vped, True)
    #voltage=np.zeros(5)
    #for j in range(5):
    counter=0
    while True:
        voltage=multi.read_value()*1000.
        if np.std(voltage)<0.1 or counter > 10:
            break
        else:
            time.sleep(0.05)
            counter+=1
    if counter > 0:
        print("Needed",counter+1,"trials!")
    #    print("Yeaj")
    tf_file.write("{}\t{}\t{}\n".format(vped,np.mean(voltage),np.std(voltage),temps))
    tf_file.flush()
    print("VPED {}, Voltage {:.2f} mV +- {:.2f} mV, Temp {:.1f} °C".format(vped,np.mean(voltage),np.std(voltage),temps))

tf_file.close()
module.CloseSockets()
multi.close()
