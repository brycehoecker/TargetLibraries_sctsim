#!/usr/bin/python
import sys
import numpy as np
import time
import target_driver
import matplotlib.pyplot as plt

def Efficiency(tigger_eff_duration):
    board.WriteSetting("TriggerEff_Duration", trig_eff_duration) 
    ret, done_bit = board.ReadSetting("TriggerEff_DoneBit")
    time.sleep(0.1)
    while done_bit == 0:
        ret, done_bit = board.ReadSetting("TriggerEff_DoneBit")
    ret, N = board.ReadSetting("TriggEffCounter")
    return N

initialize = False

#duration per step in s
trigger_duration = 0.1


#path to def files
defdir = "/home/cta/Software/TargetDriver/trunk/config"

#computer ip
my_ip = "192.168.0.1"

#eval board ip
board_ip = "192.168.0.123"

board_def = defdir+"/TC_EB_FPGA_Firmware0xFEDA001C.def"
asic_def = defdir+"/TC_ASIC.def"
trigger_asic_def = defdir+"/T5TEA_ASIC.def"


board = target_driver.TargetModule(board_def, asic_def, trigger_asic_def, 0)

if initialize:
    board.EstablishSlowControlLink(my_ip, board_ip)
    board.Initialise()
    board.EnableDLLFeedback()
    #board.WriteSetting("SetDataPort", 8107)
    #board.WriteSetting("SetSlowControlPort", 8201)
else:
    board.ReconnectToServer(my_ip, 8201, board_ip, 8105)


#Set Vped
for channel in range(16):
    board.WriteTriggerASICSetting("Vped_{}".format(channel),0, 1400,True)


ret, fw = board.ReadRegister(0)
print ("Firmware version: {:x}".format(fw))

#disable data trigger
board.WriteSetting("TACK_EnableTrigger",0)

#enable triggermask for efficiency scan (same as for data trigger)
board.WriteSetting("TriggerEff_Enable", 0b1)

board.WriteTriggerASICSetting("Wbias_0", 0, 985, True)
board.WriteTriggerASICSetting("Wbias_1", 0, 985, True)
board.WriteTriggerASICSetting("Wbias_2", 0, 985, True)
board.WriteTriggerASICSetting("Wbias_3", 0, 985, True)

board.WriteTriggerASICSetting("PMTref4_0", 0, 0, True)
board.WriteTriggerASICSetting("PMTref4_1", 0, 0, True)
board.WriteTriggerASICSetting("PMTref4_2", 0, 0, True)
board.WriteTriggerASICSetting("PMTref4_3", 0, 0, True)

board.WriteTriggerASICSetting("Thresh_0", 0,2000, True)
board.WriteTriggerASICSetting("Thresh_1", 0,2000, True)
board.WriteTriggerASICSetting("Thresh_2", 0,2000, True)
board.WriteTriggerASICSetting("Thresh_3", 0,2000, True)

f = open('scan.dat','w')

board.WriteTriggerASICSetting("Thresh_0",0,2000, True)

pmtref4_start=1900
pmtref4_stop=2100
stepsize = 2

countrate = np.zeros([2,int((pmtref4_stop-pmtref4_start)/stepsize)])

trig_eff_duration = int(trigger_duration / 8. * 1e9)

index = 0

for pmtref4 in range(pmtref4_start,pmtref4_stop,stepsize):
    board.WriteTriggerASICSetting("PMTref4_0",0,pmtref4, True)
    time.sleep(0.01)
    counts=Efficiency(trig_eff_duration)
    rate=counts/trigger_duration/1000
    print ("PMTref4",pmtref4," Counts ",counts, " Rate in kHz",rate)
    countrate[0,index]=pmtref4
    countrate[1,index]=rate
    f.write(str(pmtref4)+"\t"+str(counts)+"\t"+str(rate)+"\n")
    index=index+1

f.close()
board.WriteSetting("TACK_EnableTrigger",0x10000)

board.CloseSockets()


f, ax = plt.subplots(1, sharex=True)
#ax = plt.subplot(211)
ax.set_title("Trigger Rate vs PMTref4 at Thresh = 2000")
ax.scatter(countrate[0],countrate[1])
plt.xlabel('PMTref4 [ADC]')
plt.ylabel('Trigger rate [kHz]')
plt.show()