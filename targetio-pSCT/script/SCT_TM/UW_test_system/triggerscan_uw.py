#!/usr/bin/python
import sys
import numpy as np
import time
import target_driver
import matplotlib.pyplot as plt

#Wisconsin specific modules:
import powerCycle

bps = powerCycle.powerCycle()




#This function starts the trigger counter, by defining the duration of the count period. 
#The DoneBit (bit 31) will be set high, once the count period is elapsed and the counter is done.
def Efficiency(tigger_eff_duration):
    board.WriteSetting("TriggerEff_Duration", trig_eff_duration)
    ret, done_bit = board.ReadSetting("TriggerEff_DoneBit")
    time.sleep(0.1)
    while done_bit == 0:
        ret, done_bit = board.ReadSetting("TriggerEff_DoneBit")
    ret, N = board.ReadSetting("TriggEffCounter")
    return N - 1




#Define if new initialization is needed:
initialize = True

#duration of trigger count period in s
trigger_duration = 1


#path to def files
board_def = "/Users/brent/TargetDriver_issue37423/config/SCT_MSA_FPGA_Firmware0xC0000001.def"
asic_def = "/Users/brent/TargetDriver_issue37423/config/TC_ASIC.def"
trigger_asic_def = "/Users/brent/TargetDriver_issue37423/config/T5TEA_ASIC.def"
#computer ip
my_ip = "192.168.12.1"
#eval board ip
board_ip = "192.168.12.173"


#Define the targetModule object
board = target_driver.TargetModule(board_def, asic_def, trigger_asic_def, 0)


if initialize:
    #In case of a reinitialization an connection needs to be established to the targetModule. It needs to be reset and all default parameters need to be written.
    board.EstablishSlowControlLink(my_ip, board_ip)
    board.Initialise()
    board.EnableDLLFeedback()
else:
    board.ReconnectToServer(my_ip, 8201, board_ip, 8105)
    #board.WriteSetting("SetDataPort", 8107)
    #board.WriteSetting("SetSlowControlPort", 8201)


#Set Vped
for channel in range(16):
    board.WriteTriggerASICSetting("Vped_{}".format(channel),0, 1500,False)

#board.SetVerbose()

ret, fw = board.ReadRegister(0)
print ("Firmware version: {:x}".format(fw))

#disable data trigger
board.WriteSetting("TACK_EnableTrigger",0)

#enable triggermask for efficiency scan (same as for data trigger)



#board.WriteTriggerASICSetting("TRGsumbias", 0, 0x640, True)

board.WriteTriggerASICSetting("Wbias_0", 0, 1085, False)
board.WriteTriggerASICSetting("Wbias_1", 0, 1085, False)
board.WriteTriggerASICSetting("Wbias_2", 0, 1085, False)
board.WriteTriggerASICSetting("Wbias_3", 0, 1085, False)

board.WriteTriggerASICSetting("PMTref4_0", 0, 2130, False)
board.WriteTriggerASICSetting("PMTref4_1", 0, 2130, False)
board.WriteTriggerASICSetting("PMTref4_2", 0, 2130, False)
board.WriteTriggerASICSetting("PMTref4_3", 0, 2130, False)

board.WriteTriggerASICSetting("Thresh_0", 0,0, False)
board.WriteTriggerASICSetting("Thresh_1", 0,0, False)
board.WriteTriggerASICSetting("Thresh_2", 0,0, False)
board.WriteTriggerASICSetting("Thresh_3", 0,0, False)

board.WriteTriggerASICSetting("TTbias_A", 0,0x443, False)
#board.WriteTriggerASICSetting("AmonSelect", 0,1, False)


pmtref4_start=1500
pmtref4_stop=2000
stepsize = 10

countrate = np.zeros([2,int((pmtref4_stop-pmtref4_start)/stepsize)])

trig_eff_duration = int(trigger_duration / 8. * 1e9)



for group in range(8,9):
    board.WriteSetting("TriggerEff_Enable", 2**group)
    filename='scan_'+str(group)+'.dat'
    f = open(filename,'w')
    index = 0
    for pmtref4 in range(pmtref4_start,pmtref4_stop,stepsize):
        pmtref4_name='Thresh_'+str(int(group%4))
        board.WriteTriggerASICSetting(pmtref4_name,int(group/4),pmtref4, True)
        time.sleep(0.01)
        counts=Efficiency(trig_eff_duration)
        rate=counts*1.0/trigger_duration/1000
        print ("group",group,"PMTref4",pmtref4," Counts ",counts, " Rate in kHz",rate)
        countrate[0,index]=pmtref4
        countrate[1,index]=rate
        f.write(str(pmtref4)+"\t"+str(counts)+"\t"+str(rate)+"\n")
        index=index+1
    board.WriteTriggerASICSetting(pmtref4_name,int(group/4),0, True)
    f.close()
#    f, ax = plt.subplots(1, sharex=True)
    #ax = plt.subplot(211)
#    ax.set_title("Trigger Rate vs Thresh at PMTref4 = 2130")
#    ax.scatter(countrate[0],countrate[1])
 #   ax.set_yscale('log')
    #ax.set_ylim(0.1,1e8)
    #plt.xlabel('PMTref4 [ADC]')
    #plt.ylabel('Trigger rate [kHz]')


board.CloseSockets()
powerCycle.powerOff(bps)
#plt.show()
