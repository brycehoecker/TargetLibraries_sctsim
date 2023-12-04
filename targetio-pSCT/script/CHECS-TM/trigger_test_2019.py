import target_driver
import target_io
import time
from astropy.io import ascii
import os
import sys



# Duration in seconds
def GetSPCount(duration=1, sp=0):
    module.WriteSetting("TriggerEff_Enable", 2**sp)
    trig_eff_duration=int(duration/8e-9)
    module.WriteSetting("TriggerEff_Duration", trig_eff_duration) 
    ret, done_bit = module.ReadSetting("TriggerEff_DoneBit")
    time.sleep(0.1)
    while done_bit == 0:
        ret, done_bit = module.ReadSetting("TriggerEff_DoneBit")
    ret, N = module.ReadSetting("TriggEffCounter")
    #N = N-1 # fixed in firmware version 14 or fix in TargetDriver when resetting the counters????
    return N

def MonitorSPCount(t0,fname='spcount.dat'):
    values = []
    f = open(fname,'a')
    dt = time.time() - t0
    f.write('%i ' % dt)
    values.append(int(dt))
    for sp in range(16):
        N = GetSPCount(1, sp)
        values.append(int(N))
        f.write('%i ' % N)   
    f.flush()
    f.close()
    print('Trigger Counters are',values)

def PrintTemps(fname='spcount.dat') :
    ######### Read Temperatures #############
    temps = []
    f = open(fname,'a')
    ret,temp =  module.GetTempI2CPrimary()
    temps.append(temp)
    f.write('Pri %f ' % temp)
    print ("Temperature Pri: ",temp)
    ret, temp =  module.GetTempI2CAux()
    temps.append(temp)
    f.write('Aux %f ' % temp)
    print ("Temperature Aux: ",temp)
    ret, temp =  module.GetTempI2CPower()
    temps.append(temp)
    f.write('Pow %f ' % temp)
    print ("Temperature Pow: ",temp)
    ret, temp =  module.GetTempSIPM()
    temps.append(temp)
    f.write('SiPM %f ' % temp)
    print ("Temperature SiPM: {:3.2f}".format(temp))
    f.write('\n') 
    f.flush()
    f.close()

def PrintSiPMValues(fname='SiPMMonitoring.dat'):
    for sp in range(16):
        ret, hv = module.GetHVSuperPixel(sp)
        print(hv," ")
    ret, cur = module.ReadHVCurrentInput()
    print(cur)
    
def ScanPMTRef4(sp=0,duration=0.05,thresh=2000,pmtref_start=1800,pmtref_stop=2500,pmtref_step=20):
    module.WriteSetting("TriggerEff_Enable", 2**sp)
    print("\n\n=======================")
    print("Group",sp,"Thresh",thresh)
    print("=======================")
    print("PMTref4 Counts Rate")
    print("-------------------")
    filename="trigger_scan_thresh_"+str(thresh)+"_sp_"+str(sp)+".txt"
    f1 = open(filename,'w')
    module.WriteTriggerASICSetting("Thresh_"+str(int(sp%4),int(sp/4), thresh, True))
    settingname = "PMTref4_"+str(int(sp%4))
    for pmtref in range(int(pmtref_start),int(pmtref_stop),int(pmtref_step)):
        module.WriteTriggerASICSetting(settingname, int(sp/4), pmtref, True)
        time.sleep(0.01)
        counts=GetSPCount(duration,sp)
        rate=counts/float(duration)
        print(pmtref,counts,rate)
        f1.write(str(pmtref)+"\t"+str(counts)+"\t"+str(rate)+"\n")
    module.WriteTriggerASICSetting(settingname, int(sp/4), 0, True)
    f1.close()

######### Measure the HV DACs #############
def read_HVDAC():
  for channel in range (0,16) :
    ret, answer = module.ReadSetting("HV{}_Voltage".format(channel))
    if answer < 0x8000 :
      answer = answer + 0x8000
    else :
      answer = answer & 0x7FFF
    print ("HV SuperPixel {0} :\t{1:3.2f}".format(channel, answer *0.03815*2*20/1000))



my_ip = "192.168.12.1"
module_ip = "192.168.12.173"
initialize = True

module_def = "/home/cta/Software/TargetSuite/source/TargetDriver/config/TC_MSA_FPGA_Firmware0xC000000D.def"
asic_def = "/home/cta/Software/TargetSuite/source/TargetDriver/config/TC_ASIC.def"
trigger_asic_def = "/home/cta/Software/TargetSuite/source/TargetDriver/config/T5TEA_ASIC.def"

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

for asic in range(4):
  module.WriteTriggerASICSetting("VpedBias", asic, 1800, True)
  for group in range(4):
    module.WriteTriggerASICSetting("Wbias_{}".format(group), asic, 985, True)
  for channel in range(16):
    module.WriteTriggerASICSetting("Vped_{}".format(channel), asic, 1200, True)
time.sleep(1)


for asic in range(4):
    module.WriteSetting("EnableChannelsASIC{}".format(asic), 0xffff)
module.WriteSetting("Zero_Enable", 0x1)
module.WriteSetting("DoneSignalSpeedUp",0)
nblocks = 8
module.WriteSetting("NumberOfBlocks", nblocks-1)
module.WriteSetting("MaxChannelsInPacket", 4)

module.WriteSetting("TACK_TriggerType", 0x0)
module.WriteSetting("TACK_TriggerMode", 0x0)
module.WriteSetting("TACK_EnableTrigger", 0x0)

print ("\nEnabling Slow ADCs\n")
module.WriteSetting("SlowADCEnable_Primary",1)
module.WriteSetting("SlowADCEnable_Aux",1)
module.WriteSetting("SlowADCEnable_Power",1)

thresh=2000

module.WriteTriggerASICSetting("Thresh_0", 0, thresh, False)
module.WriteTriggerASICSetting("Thresh_1", 0, thresh, False)
module.WriteTriggerASICSetting("Thresh_2", 0, thresh, False)
module.WriteTriggerASICSetting("Thresh_3", 0, thresh, False)

module.WriteTriggerASICSetting("PMTref4_0", 0, 2300, False)
module.WriteTriggerASICSetting("PMTref4_1", 0, 2300, False)
module.WriteTriggerASICSetting("PMTref4_2", 0, 2300, False)
module.WriteTriggerASICSetting("PMTref4_3", 0, 2300, False)

hval = [38,62,59,65,36,45,46,58,66,32,54,54,55,67,58,64,]

module.DisableHVAll()
for superpixel in range(0,16):
    module.SetHVDAC(superpixel,hval[superpixel])
    module.EnableHVSuperPixel(superpixel)
    #print("Enabled SP",superpixel)
    #time.sleep(1)
print ("let HV settle")

time.sleep(3)


read_HVDAC()

t0 = time.time()

for i in range(int(3600/16)):
    MonitorSPCount(t0)
    PrintTemps()
    PrintSiPMValues()
    
