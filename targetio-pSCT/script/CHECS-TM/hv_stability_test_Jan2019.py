'''
script to test the HV and trigger stability for one TM
@author: Justus Zorn (MPIK)
Jan 2019
'''

import target_driver
import target_io
import time
import os
import sys

sys.path.append('/home/cta/MPIKLabSoftware/ESPEC_LU114_ThermalChamber/')
import ESPEC_LU114_ThermalChamber


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
    f.write('\n') 
    f.flush()
    f.close()
    print('Trigger Counters are',values)

def PrintTemps(t0,fname='temp.dat') :
    ######### Read Temperatures #############
    temps = []
    f = open(fname,'a')
    ret,temp =  module.GetTempI2CPrimary()
    temps.append(temp)
    dt = time.time() - t0
    f.write('%i ' % dt)
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
    ret, answer = module.ReadHVCurrentInput()
    temps.append(answer)
    f.write('currentIn %f ' % answer)
    print ("Current SiPM: {:3.2f}".format(answer))
    ret, answer = module.ReadHVVoltageInput()
    temps.append(answer)
    f.write('voltageIn %f ' % answer)
    print ("Voltage SiPM: {:3.2f}".format(answer))
    f.write('\n') 
    f.flush()
    f.close()

######### Measure the HV  #############
def MonitorHVDAC(t0,fname='hv.dat'):
    f = open(fname,'a')
    dt = time.time() - t0
    f.write('%i ' % dt)
    for channel in range (0,16) :
        ret, answer = module.GetHVSuperPixel(channel)
        print ("HV SuperPixel", channel, answer)
        f.write('%.4f ' % answer)
    f.write('\n') 
    f.flush()
    f.close()





def setup_thermalchamber(ip,T):
    tchamber = ESPEC_LU114_ThermalChamber.ThermalChamber(ip)
    tchamber.Connect()
    tchamber.SetT(T)
    tchamber.Run()

if __name__ == "__main__":

    directory = "/home/cta/UserSpace/justus/d2019-01_CHECS-TM_StabilityTests/"


    #Add temperature chamber at some point

    

    my_ip = "192.168.12.1"
    module_ip = "192.168.12.109"
    initialize = True

    module_def = "/home/cta/Software/TargetSuite/source/TargetDriver/config/TC_MSA_FPGA_Firmware0xC000000C.def"
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

    #hval = [38,62,59,65,36,45,46,58,66,32,54,54,55,67,58,64,]
    hval = [67,61,65,61,62,45,71,62,53,58,49,50,50,76,65,49]
    module.DisableHVAll()
    for superpixel in range(0,16):
        module.SetHVDAC(superpixel,hval[superpixel])
        module.EnableHVSuperPixel(superpixel)
    print ("let HV settle")

    time.sleep(3)


    t0 = time.time()

    if os.path.isfile(directory+"d2019-01-24_hv_35degC_TM-SN0023.dat"):
        print("ERROR: Result file", directory+"d2019-01-22_hv.dat", "already exists")
        module.DisableHVAll()
        exit(-1)


    #10 hour measurement
    for i in range(36000//16): # //16 since one monitoring cycle takes 16 s
        MonitorHVDAC(t0,directory+"d2019-01-24_hv_35degC_TM-SN0023.dat")
        MonitorSPCount(t0,directory+"d2019-01-24_L1trig_35degC_TM-SN0023.dat")
        PrintTemps(t0,directory+"d2019-01-24_temp_35degC_TM-SN0023.dat")
        time.sleep(0.5)

    module.DisableHVAll()
