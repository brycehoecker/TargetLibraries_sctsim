#!/usr/bin/python
import serial
import sys
import numpy as np
import argparse
sys.path.append('/home/cta/justus/RigolPulseGenerator')
import pulsegen
sys.path.append('/home/cta/Software/TargetIO/trunk/script/common_devices')
import splitter
import time
import target_driver

def Efficiency(tigger_eff_duration):
    board.WriteSetting("TriggerEff_Duration", trig_eff_duration) 
    ret, done_bit = board.ReadSetting("TriggerEff_DoneBit")
    time.sleep(0.1)
    while done_bit == 0:
        ret, done_bit = board.ReadSetting("TriggerEff_DoneBit")
    ret, N = board.ReadSetting("TriggEffCounter")
    #N = N-1 # fixed in firmware version 14 or fix in TargetDriver when resetting the counters????
    return N


j=1

if j == 1: #scan over parameters

ser0 = serial.Serial('/dev/ttyACM0', 9600, timeout=0)
ser1 = serial.Serial('/dev/ttyACM1', 9600, timeout=0)
ser0.read(1000)
ser1.read(1000)
bitmask0 = 0xffff
bitmask1 = 0xffff
splitter.enableChannels(bitmask0,ser0)
splitter.readVoltage(ser0)
splitter.enableChannels(bitmask1,ser1)
splitter.readVoltage(ser1)

p = pulsegen.RigolPulseGen("/dev/usbtmc0")

# pulse generator settings
f_generator = 100  # Hz
f_width = 10  # ns
f_rt = 3  # ns
f_ft = 3  # ns

trigger_duration = 1
trig_eff_duration = int(trigger_duration / 8. * 1e9)

p.write(':SOUR1:PULS:WIDT %ins' % f_width)
p.write(':SOURC1:PULS:TRAN:LEAD %ins' % f_rt)
p.write(':SOURC1:PULS:TRAN:TRA %ins' % f_ft)

my_ip = "192.168.12.1"
module_ip = "192.168.12.173"

module_def = "/home/cta/Software/TargetDriver/branches/issue17073/config/TC_MSA_FPGA_Firmware0xC0000003.def"
asic_def = "/home/cta/Software/TargetDriver/branches/issue17073/config/TC_ASIC.def"
trigger_asic_def = "/home/cta/Software/TargetDriver/branches/issue17229/config/T5TEA_ASIC.def"

module = target_driver.TargetModule(module_def, asic_def, trigger_asic_def, 0)
module.SetClientIP(my_ip)
module.SetModuleIP(module_ip)
module.Connect()
module.Initialise()
module.EnableDLLFeedback()
print "module initialized"

ret, fw = module.ReadRegister(0)
print "Firmware version: {:x}".format(fw)

#module.WriteSetting("SetSlowControlPort", 8201)

print "Slow control port set"

nblocks = 2

module.WriteASICSetting("WR_ADDR_Incr1LE_Delay", 0, 55+2 )
module.WriteASICSetting("WR_ADDR_Incr1TE_Delay", 0, 6+2 )
module.WriteASICSetting("WR_ADDR_Incr2LE_Delay", 0, 55+2 )
module.WriteASICSetting("WR_ADDR_Incr2TE_Delay", 0, 6+2 )

module.WriteSetting("TriggerDelay", 4000)
module.WriteSetting("TACK_TriggerType", 0x0)
module.WriteSetting("TACK_TriggerMode", 0x0)
module.WriteSetting("EnableChannelsASIC0", 0b1111111111111111) # take data from all 16 channels
module.WriteSetting("EnableChannelsASIC1", 0b1111111111111111) # take data from all 16 channels
module.WriteSetting("EnableChannelsASIC2", 0b1111111111111111) # take data from all 16 channels
module.WriteSetting("EnableChannelsASIC3", 0b1111111111111111) # take data from all 16 channels
module.WriteSetting("Zero_Enable", 0x1)
module.WriteSetting("NumberOfBlocks", nblocks)
module.WriteSetting("MaxChannelsInPacket", 16) # only one packet for all channels


for asic in range(4):
    module.WriteTriggerASICSetting("VpedBias",asic, 1800,True)
    for channel in range(16):
        module.WriteTriggerASICSetting("Vped_{}".format(channel),asic,1000,True)
'''
for asic in range(4):
    module.WriteSetting("EnableChannelsASIC{}".format(asic), 0xffff)
'''
module.WriteSetting("DoneSignalSpeedUp",0)
module.WriteSetting("TACK_EnableTrigger",0)
module.WriteSetting("TriggerEff_Enable", 0xFFFF)

module.WriteTriggerASICSetting("PMTref4_0", 0, 1840, False)
module.WriteTriggerASICSetting("PMTref4_1", 0, 1840, False)
module.WriteTriggerASICSetting("PMTref4_2", 0, 1840, False)
module.WriteTriggerASICSetting("PMTref4_3", 0, 1840, False)
t=0
while (t<4000):
    module.WriteTriggerASICSetting("Thresh_0", 0, t, False)
    module.WriteTriggerASICSetting("Thresh_1", 0, t, False)
    module.WriteTriggerASICSetting("Thresh_2", 0, t, False)
    module.WriteTriggerASICSetting("Thresh_3", 0, t, False)
    #
    module.WriteSetting("TriggerCounterReset", 1)
    #
    p.write(':OUTP1:STAT ON')
    time.sleep(1)
    module.WriteSetting("TriggerEff_Duration", trig_eff_duration)  # counting time in 8 ns
    done_bit = 0
    while done_bit == 0:
        ret, done_bit = module.ReadSetting("TriggerEff_DoneBit")
        time.sleep(1e-1)
        print done_bit
    ret, N = module.ReadSetting("TriggEffCounter")
    N = N - 1
    print "N = ", N
    p.write(':OUTP1:STAT OFF')
    t+=200

eff = float(N) / (trigger_duration * f_generator)



f = open('/home/cta/scan.dat','w')
f.write('# Scan through PMTref4 and Thresh\n')
f.write('# ASIC SP PMTref4 Thresh eff\n')
f.close()

trig_eff_duration = int(trigger_duration / 8. * 1e9)

ampl_min = 1
ampl_max = 47
ampl_step = 5

ampl = np.arange(ampl_min, ampl_max, ampl_step)

# to get the appropriate pulse heights, use a 10dB attenuator!
# from the fit ampl_asic_in = p[0]*ampl_pulsegen_out + p[1] --> p[0] = 0.30731169, p[1] = -0.10890475 (see /home/cta/justus/T5TEA_tests/attenuation_measurement/attenuation_10db.txt
ampl_out = (ampl + 0.10890475) / 0.30731169 * 1e-3  #devided by 0.9 because dividing pulse reduces amplitude to module by 0.1


f = open('/home/cta/scan.txt','a')
#


#
for asic in range(2):#has to be changed when connecting to other board

    for superpixel in range(4):
        for t in range(0,4095,32):
            for pref in range(0,4095,32):
                for a in ampl_out:
                    p.write(':SOUR1:APPL:PULS %i,%f,0,0' % (f_generator, a))  # apply square, frequency,amplitude,DC offset,start phase
                    p.write(':OUTP1:STAT ON')
                    time.sleep(2) #important in order to ensure that the trigger pulses from the pulse generator arrives at the trigger input of the ASIC when it starts to count the triggers

                    module.WriteTriggerASICSetting("PMTref4_{}".format(superpixel), asic, pref, True)
                    module.WriteTriggerASICSetting("Thresh_{}".format(superpixel), asic, t, True)
                    #
                    module.WriteSetting("TriggerCounterReset", 1)
                    ret, done_bit = module.ReadSetting("TriggerEff_DoneBit") #done_bit should be 0 here!
                    #
                    module.WriteSetting("TriggerEff_Duration", trig_eff_duration)  # counting time in 8 ns
                    ret, done_bit = module.ReadSetting("TriggerEff_DoneBit")
                    time.sleep(0.1)
                    while done_bit == 0:
                        ret, done_bit = module.ReadSetting("TriggerEff_DoneBit")
                    p.write(':OUTP1:STAT OFF')
                    ret, N = module.ReadSetting("TriggEffCounter")
                    N = N - 1
                    eff = float(N) / (trigger_duration * f_generator)

                    f.write('%i %i %i %i %f\n' % (asic, superpixel, pref,t,eff))

        module.WriteTriggerASICSetting("PMTref4_{}".format(superpixel), asic, 0, True)
        module.WriteTriggerASICSetting("Thresh_{}".format(superpixel), asic, 0, True)


f.close()




if j == 2: #measure trigger efficiency for one given amplitude

    parser = argparse.ArgumentParser(description='T5TEA Efficiency Tests')
    parser.add_argument('initialized', type=int,
                        help='if the board is just powercycled or turned on, it must be initialized and "initialized" must be set to 0')
    args = parser.parse_args()
    initialized = args.initialized

    my_ip = "192.168.0.1"
    board_ip = "192.168.0.123"

    board_def = "/home/cta/TARGET/TargetDriver/config/TECT5TEA_FPGA_Firmware0xFEDA0008.def"
    ASIC_def = "/home/cta/TARGET/TargetDriver/config/TEC_ASIC.def"
    TriggerASIC_def = "/home/cta/TARGET/TargetDriver/config/T5TEA_ASIC.def"

    # initial board and pulse generator configuration
    board = target_driver.TargetModule(board_def, ASIC_def, TriggerASIC_def, 0)
    p = pulsegen.RigolPulseGen("/dev/usbtmc0")

    PMTref4 = 1955
    Thresh = 3000
    trigger_group = 0
    trigger_channel = 4
    trigger_duration = 8  # s


    # pulse generator settings
    ampl = 1500
    f_generator = 10000  # Hz
    f_width = 10  # ns
    f_rt = 3  # ns
    f_ft = 3  # ns

    p.write(':SOUR1:PULS:WIDT %ins' % f_width)
    p.write(':SOURC1:PULS:TRAN:LEAD %ins' % f_rt)
    p.write(':SOURC1:PULS:TRAN:TRA %ins' % f_ft)
    ampl_out = (ampl + 0.10890475) / 0.30731169 * 1e-3  # from the fit ampl_asic_in = p[0]*ampl_pulsegen_out + p[1] --> p[0] = 0.30731169, p[1] = -0.10890475
    p.write(':SOUR1:APPL:PULS %i,%f,0,0' % (f_generator, ampl_out))
    p.write(':OUTP1:STAT ON')

    time.sleep(2) #important in order to ensure that the trigger pulses from the pulse generator arrives at the trigger input of the ASIC when it starts to count the triggers


    if initialized == 0:
        board.EstablishSlowControlLink(my_ip, board_ip)
        board.Initialise()
        time.sleep(1)
        board.EnableDLLFeedback()
    else:
        board.ReconnectToServer(my_ip, 8201, board_ip, 8105)

    board.WriteSetting("Vped_value", 1100)

    if trigger_group == 0:
        board.WriteSetting("TriggerEff_Enable", 1)
        board.WriteTriggerASICSetting("PMTref4_0", 0, PMTref4, True)
        board.WriteTriggerASICSetting("Thresh_0", 0, Thresh, True)
    elif trigger_group == 1:
        board.WriteSetting("TriggerEff_Enable", 2)
        board.WriteTriggerASICSetting("PMTref4_1", 0, PMTref4, True)
        board.WriteTriggerASICSetting("Thresh_1", 0, Thresh, True)
    elif trigger_group == 2:
        board.WriteSetting("TriggerEff_Enable", 4)
        board.WriteTriggerASICSetting("PMTref4_2", 0, PMTref4, True)
        board.WriteTriggerASICSetting("Thresh_2", 0, Thresh, True)
    elif trigger_group == 3:
        board.WriteSetting("TriggerEff_Enable", 8)
        board.WriteTriggerASICSetting("PMTref4_3", 0, PMTref4, True)
        board.WriteTriggerASICSetting("Thresh_3", 0, Thresh, True)

    trig_eff_duration = int(trigger_duration / 8. * 1e9)


    board.WriteSetting("TriggerEff_Duration", trig_eff_duration)  # counting time in 8 ns
    ret, done_bit = board.ReadSetting("TriggerEff_DoneBit")
    time.sleep(0.1)
    while done_bit == 0:
        ret, done_bit = board.ReadSetting("TriggerEff_DoneBit")
    p.write(':OUTP1:STAT OFF')
    ret, N = board.ReadSetting("TriggEffCounter")
    N = N - 1
    eff = float(N) / (trigger_duration * f_generator)
    print ampl, N, eff
