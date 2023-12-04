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
    return N - 1

initialize = True

#duration per step in s
trigger_duration = 0.1


#path to def files
board_def = "/home/target5/Software/TargetDriver/trunk/config/SCT_MSA_FPGA_Firmware0xC0000001.def"
asic_def = "/home/target5/Software/TargetDriver/trunk/config/TC_ASIC.def"
trigger_asic_def = "/home/target5/Software/TargetDriver/trunk/config/T5TEA_ASIC.def"
#computer ip
my_ip = "192.168.12.1"

#eval board ip
board_ip = "192.168.12.173"



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
    board.WriteTriggerASICSetting("Vped_{}".format(channel),0, 1500,False)


ret, fw = board.ReadRegister(0)
print ("Firmware version: {:x}".format(fw))

#disable data trigger
board.WriteSetting("TACK_EnableTrigger",0)

#enable triggermask for efficiency scan (same as for data trigger)


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

pmtref4_start=1950
pmtref4_stop=2060
stepsize = 2

countrate = np.zeros([2,int((pmtref4_stop-pmtref4_start)/stepsize)])

trig_eff_duration = int(trigger_duration / 8. * 1e9)



for group in range(4,16):
    board.WriteSetting("TriggerEff_Enable", 2**group)
    filename='scan_'+str(group)+'.dat'
    f = open(filename,'w')
    index = 0
    for pmtref4 in range(pmtref4_start,pmtref4_stop,stepsize):
        pmtref4_name='PMTref4_'+str(int(group%4))
        board.WriteTriggerASICSetting(pmtref4_name,int(group/4),pmtref4, True)
        time.sleep(0.01)
        counts=Efficiency(trig_eff_duration)
        rate=counts/trigger_duration/1000
        print ("group",group,"PMTref4",pmtref4," Counts ",counts, " Rate in kHz",rate)
        countrate[0,index]=pmtref4
        countrate[1,index]=rate
        f.write(str(pmtref4)+"\t"+str(counts)+"\t"+str(rate)+"\n")
        index=index+1
    board.WriteTriggerASICSetting(pmtref4_name,int(group/4),0, True)
    f.close()
    f, ax = plt.subplots(1, sharex=True)
    #ax = plt.subplot(211)
    ax.set_title("Trigger Rate vs PMTref4 at Thresh = 2000")
    ax.scatter(countrate[0],countrate[1])
    plt.xlabel('PMTref4 [ADC]')
    plt.ylabel('Trigger rate [kHz]')
    plt.show()


board.CloseSockets()
