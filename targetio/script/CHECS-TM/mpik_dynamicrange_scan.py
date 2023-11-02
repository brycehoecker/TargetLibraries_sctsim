# -*- coding: utf-8 -*-
"""
TARGET Module dynamic range scan with filter wheel at MPIK
     @author: Justus Zorn (MPIK)
"""


import argparse
import os.path
import os
import sys
import numpy as np
from termcolor import colored
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import target_io
import target_driver
from tqdm import tqdm
import time

sys.path.append('/home/cta/MPIKLabSoftware/FilterWheel/')
import FilterWheel

sys.path.append('/home/cta/MPIKLabSoftware/BNC_577_PulseGen/')
import PulseGenerator

sys.path.append('/home/cta/MPIKLabSoftware/LEDControl/')
import LEDControl


global nmaxchan, nblocks
nmaxchan = 1
nblocks = 4

###########################################################################################
def setup_tm(my_ip='192.168.12.1', tm_ip='192.168.12.131', delay=300):
    vpedbias = 1100  # DAC offset value, 0:4096
    vped_ = 1200  # real 0:4096, 0 to lower the ped, 4096 higher ped
    PMTref4 = 0  # 1800
    thresh = 50

    nsdeadtime = 0  # 62500
    sr_disabletrigger = 1  # disable further triggers during a readout, 0:1

    # triggerdelay = 425 # Value needed in thermal chamber
    triggerdelay = delay  # was270 # delay to wait before readout of waveform***, 0:32767, ns

    module_def = "/home/cta/Software/TargetDriver/trunk/config/TC_MSA_FPGA_Firmware0xC0000008.def"
    asic_def = "/home/cta/Software/TargetDriver/trunk/config/TC_ASIC.def"
    trigger_asic_def = "/home/cta/Software/TargetDriver/trunk/config/T5TEA_ASIC.def"

    tm = target_driver.TargetModule(module_def, asic_def, trigger_asic_def, 0)
    tm.EstablishSlowControlLink(my_ip, tm_ip)
    tm.Initialise()
    ret, fw = tm.ReadRegister(0)
    print("\nFirmware version: {:x}".format(fw))
    tm.EnableDLLFeedback()

    print("\nmodule initialized\n")

    # Disable trigger
    tm.WriteSetting("TACK_EnableTrigger", 0)
    tm.DisableHVAll()

    ######### Read firmware version #############
    ret, fw = tm.ReadRegister(0)
    print("\nFirmware version: {:x}".format(fw))

    tm.WriteTriggerASICSetting("VpedBias", 0, vpedbias, True)
    tm.WriteTriggerASICSetting("VpedBias", 1, vpedbias, True)
    tm.WriteTriggerASICSetting("VpedBias", 2, vpedbias, True)
    tm.WriteTriggerASICSetting("VpedBias", 3, vpedbias, True)

    for channel in range(16):
        tm.WriteTriggerASICSetting("Vped_{}".format(channel), 0, vped_, True)  # ASIC 0
        tm.WriteTriggerASICSetting("Vped_{}".format(channel), 1, vped_, True)  # ASIC 1
        tm.WriteTriggerASICSetting("Vped_{}".format(channel), 2, vped_, True)  # ASIC 2
        tm.WriteTriggerASICSetting("Vped_{}".format(channel), 3, vped_, True)  # ASIC 3

    ######### Enable the channels and settings #############
    tm.WriteSetting("EnableChannelsASIC0", 0b1111111111111111)  # Enable or disable 16 channels
    tm.WriteSetting("EnableChannelsASIC1", 0b1111111111111111)
    tm.WriteSetting("EnableChannelsASIC2", 0b1111111111111111)
    tm.WriteSetting("EnableChannelsASIC3", 0b1111111111111111)

    tm.WriteSetting("Zero_Enable", 0x1)  # data trasnfer, leave at 1?
    tm.WriteSetting("DoneSignalSpeedUp", 0)  # digitiser ramp stop, needed for high rates only?
    tm.WriteSetting("NumberOfBlocks", nblocks)
    tm.WriteSetting("MaxChannelsInPacket", nmaxchan)

    # tm.WriteASICSetting("Vdischarge",2, 1000,True)
    # tm.WriteASICSetting("Isel",2, 1700,True)
    tm.WriteRegister(0x5f, nsdeadtime)
    tm.WriteSetting("SR_DisableTrigger", sr_disabletrigger)

    ######### Set PMTref and thresholds #############
    # Thresh sets the threshold, it's inverted so 0 is the maximum
    tm.WriteTriggerASICSetting("PMTref4_0", 0, PMTref4, True)  #
    tm.WriteTriggerASICSetting("Thresh_0", 0, thresh, True)

    ######### Setup triggering ################
    # Trigger info:
    # For External clocked pulse to trigger (Pulse, 10ms period, 2V, width <10us)
    #	ExtTriggerDirection=0, TACK_EnableTrigger=0x10000
    tm.WriteSetting("TriggerDelay", triggerdelay)  # lookback time between instant when the trigger is issued and the portion of the ASIC storage to digitize

    return tm

###########################################################################################
def control_hv_on(tm, HV_calib):
    for i in range(16):
        print(i,HV_calib[i])
        tm.SetHVDAC(i, HV_calib[i])  # superpixel 0 to 15
    print("Turn on HV and let settle.....\n")
    tm.EnableHVAll()
    time.sleep(2)  # wait
    print("HV current", tm.ReadHVCurrentInput())


### ########################################################################################
def control_hv_off(tm):
    tm.DisableHVAll()


###########################################################################################
def acquire_data_fast(tm, my_ip, take_PED, tm_id, datafolder, runnumber,acquire_time,mode=-1,pg=-1):
    if take_PED:
        datafile = 'data_PED.tio'
    else:
        datafile = 'Run' + str.zfill(str(runnumber),5) + '_r0.tio'

    kNPacketsPerEvent = 64  # by default we have a data packet for each channel, this can be changed
    kPacketSize = target_driver.DataPacket_CalculatePacketSizeInBytes(nmaxchan, 32 * (nblocks + 1))
    kBufferDepth = 1000
    os_command = "rm {0}".format(datafolder + datafile)
    os.system(os_command)
    listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
    listener.AddDAQListener(my_ip)
    listener.StartListening()
    writer = target_io.EventFileWriter(datafolder + datafile, kNPacketsPerEvent, kPacketSize)
    buf = listener.GetEventBuffer()
    writer.StartWatchingBuffer(buf)

    print("\nAcquiring data...\a")
    ######### Start data taking ###################

    if mode == 2 or mode == 3:
        delay_start = 31
        pg.activate()
        for block_phase in range(0,32):
            tm.WriteSetting("TriggerDelay", delay_start-block_phase)
            pg.set_ch(2,1,3.5,200,block_phase)
            tm.WriteSetting("TACK_EnableTrigger", 0x10000)  #
            time.sleep(acquire_time/10)
            tm.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers
        pg.deactivate()
    else:
        tm.WriteSetting("TACK_EnableTrigger", 0x10000)  #
        time.sleep(acquire_time)  # wait to accumulatedata
        tm.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers

    writer.StopWatchingBuffer()  # stops data storing in file
    buf.Flush()
    print("Output file: {}\a".format(datafolder + datafile))
    writer.Close()
    tm.WriteSetting("ExtTriggerDirection", 0x1)  # uses sync output for triggering

    if take_PED:
        ######### Generate PED ###################
        os_command = "/home/cta/Software/TargetCalib/install/./generate_ped -i {0}".format(datafolder + datafile)
        os.system(os_command)
    else:
        ######### Apply CALIBRATION ###################
        os_command = "/home/cta/Software/TargetCalib/install/./apply_calibration -i {0} -p {1}data_ped.tcal -t /home/cta/CHECDevelopment/CHECS/Operation/{2}_tf.tcal".format(
            datafolder + datafile, datafolder, tm_id)
        os.system(os_command)
        # read_data_fast()


if __name__ == "__main__":

    # def_log = "/home/cta/CameraLog/camera_dynamicrange_scan.log"
    # def_obs = "/home/cta/Software/CHECSInterface/trunk/config/observing.cfg"
    # def_obsped = "/home/cta/Software/CHECSInterface/trunk/config/observing_ped.cfg"
    #
    # parser = argparse.ArgumentParser(description="Scan FW range, externally trigger laser, take data")
    # parser.add_argument("--log", type=str, help="Log file name", default=def_log)
    # parser.add_argument("--hv", type=str, help="HV config file name; if no is given, HV is not supplied", default=None)
    # parser.add_argument("--pg_name", type=str, help="Pulse generator name, default: /dev/ttyUSB0", default="/dev/ttyUSB0")
    # parser.add_argument("--pg_rate", type=int, help="Pulse generator rate, default: 600 Hz", default=600)
    # parser.add_argument("--fw_ip", type=str, help="Filter wheel IP, default: 192.168.0.215", default="192.168.0.215")
    # parser.add_argument("--nsbled_ip", type=str, help="Filter wheel IP, default: 149.217.3.216", default="149.217.3.216")
    # # -----------------------------------------------------
    # # Not defined yet - done in script directly
    #
    # #parser.add_argument("--pe_start", type=int, help="FW attenuation in p.e. to start from, default: 1", default=10)
    # #parser.add_argument("--pe_stop", type=int, help="FW attenuation in p.e. to stop, default: 1000", default=256)
    # #parser.add_argument("--pe_step", type=int, help="DAC steps, default: 10", default=1)
    # # ------------------------------------------------------------
    # parser.add_argument('--with_nsbled', action='store_true', help='also uses the NSB LED')
    # parser.add_argument("--nsb_rate", type=float, help="NSB rate in MHz, default: 50", default=50)
    # parser.add_argument("--obs", type=str, help="Observing file name", default=def_obs)
    # parser.add_argument("--obsped", type=str, help="Observing file name for pedestal (mode == 2)", default=def_obsped)
    # parser.add_argument("--ped", type=str,
    #                     help="Pedestal (tcal) file name - if not specified then will be created",
    #                     default=None)
    # parser.add_argument("--laser_warm", action='store_true', help='if laser was already warmed up for at least 10 minutes')
    # parser.add_argument("--no_calibration", action='store_true', help='if runs should not be calibrated from R0 to R1 at the end using pedestal file')
    # parser.add_argument("--out", type=str, help="Resulting runlist with information", default="runlist.txt")
    # args = parser.parse_args()
    #
    # # Should run some checks on the arguments...
    # flog_name = args.log
    # fobs_name = args.obs
    # fobsped_name = args.obsped
    # fhv_name = args.hv
    # #mode = args.mode
    # fw_ip = args.fw_ip
    # pg_name = args.pg_name
    # fped_name = args.ped
    # #pe_start = args.pe_start
    # #pe_stop = args.pe_stop
    # #pe_step = args.pe_step
    # nsbled_ip = args.nsbled_ip
    # with_nsbled = args.with_nsbled
    # nsb_rate = args.nsb_rate
    # laser_warm = args.laser_warm
    # runlist = args.out
    # pgrate = args.pg_rate
    # no_calibration = args.no_calibration

    # if not os.path.isfile(fhv_name):
    #     print ("Error, HV file doesn not exist (%s)" % fhv_name)
    #     exit()

    with_nsbled = False

    mode = 1

    fw_ip = "192.168.0.215"
    print(colored("Connecting to FilterWheel", 'yellow'))
    fw = FilterWheel.FilterWheel(ip=fw_ip)
    fw.initialise()

    if mode == 2 or mode == 3:
        pg_name = "/dev/ttyUSB1"
        pg = PulseGenerator.PulseGeneratorCommunicator()
        pg.connect(name=pg_name)

        

    #Still to be adjusted!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #pe = np.arange(pe_start,pe_stop,pe_step)
    #obs_atten = np.asarray([1.0, 10.0, 100.0, 1e3, 1e4, 2e4])
    obs_atten = np.logspace(0, 1, 20, endpoint=False)
    obs_atten = np.concatenate((obs_atten,np.logspace(1, 2, 20, endpoint=False)))
    obs_atten = np.concatenate((obs_atten,np.logspace(2, 3, 10, endpoint=False)))
    #obs_atten = np.concatenate((obs_atten,np.logspace(3, 4, 10)))

    n_run = len(obs_atten)

    obs_pe = fw.get_pe(obs_atten)
    print(obs_pe)
    acquire_time = np.zeros(n_run,dtype=int)
    for i in range(len(obs_atten)):
        if obs_pe[i] < 5:
            #acquire_time[i] = 30
            acquire_time[i] = 2
        else:
            acquire_time[i] = 2

    takedata = True

    print("------------------------------------------------------")
    print(colored("Running FW sweep in acquire mode", attrs=['bold']))
    print(colored("--> The camera needs to be in Ready", 'yellow'))
    print("------------------------------------------------------")

    if with_nsbled:
        print(colored("Connecting to NSB LED, setting the DAC value and enabling to warm up", 'yellow'))
        lc = LEDControl.LEDControl(host=nsbled_ip)
        lc.set_rate(0, rate*1e6)
        lc.enable(0)

    if mode == 3:
        #50 mV gain matching values
        #dac_old = [46, 61, 37, 43, 31, 32, 28, 41, 67, 47, 66, 55, 50, 52, 60, 50]
        #datafolder = "/d2/singleTM_tests/d2018-09-19-SingleTM-SN0041-dynamicrange-scan/50mV-50pe-different-blockphases-SP-8-9/"
        
        #100 mV gain matching values
        #dac_old = [35, 52, 26, 33, 21, 22, 20, 31, 53, 37, 54, 48, 39, 41, 51, 39]
        #datafolder = "/d2/singleTM_tests/d2018-09-19-SingleTM-SN0041-dynamicrange-scan/100mV-50pe-different-blockphases-SP-8-9/"

        #200 mV gain matching values
        dac_old = [21, 35, 12, 20, 8, 9, 5, 17, 36, 24, 38, 32, 27, 28, 35, 27]
        datafolder = "/d2/singleTM_tests/d2018-09-19-SingleTM-SN0041-dynamicrange-scan/200mV-50pe-different-blockphases-SP-8-9/"

        dac = [255 for i in range(16)]
        dac[8] = dac_old[8]
        dac[9] = dac_old[9]
        
    else:

        #50 mV gain matching values
        dac = [46, 61, 37, 43, 31, 32, 28, 41, 67, 47, 66, 55, 50, 52, 60, 50]
        datafolder = "/d2/singleTM_tests/d2018-09-19-SingleTM-SN0041-dynamicrange-scan/50mV-50pe-different-blockphases/"


        #100 mV gain matching values
        #dac = [35, 52, 26, 33, 21, 22, 20, 31, 53, 37, 54, 48, 39, 41, 51, 39]
        #datafolder = "/d2/singleTM_tests/d2018-09-19-SingleTM-SN0041-dynamicrange-scan/100mV-50pe-different-blockphases/"

        #200 mV gain matching values
        #dac = [21, 35, 12, 20, 8, 9, 5, 17, 36, 24, 38, 32, 27, 28, 35, 27]
        #datafolder = "/d2/singleTM_tests/d2018-09-19-SingleTM-SN0041-dynamicrange-scan/200mV-50pe-different-blockphases/"

    my_ip = '192.168.12.1'
    tm = setup_tm(my_ip=my_ip, tm_ip='192.168.12.126', delay=345)
    tm_id = "SN0041"

    print(colored("Take pedestal", 'yellow'))
    take_PED = True
    if take_PED:
        acquire_data_fast(tm, my_ip, take_PED, tm_id, datafolder, -1,60)


    print(colored("Begin scan and turn on HV", 'yellow'))

    control_hv_on(tm,dac)

    runlist = datafolder + "runlist.list"
    f = open(runlist,"w")
    f.write("run_number fw_pos fw_atten pe_expected n_events\n")
    t0 = time.time()
    for i in range(n_run):
        fwpos = fw.move(atten=obs_atten[i])
        runnumber = i

        print(colored("Step %i/%i, Run=%05i, Atten=%g, Pos=%i" % (i+1, n_run, runnumber, obs_atten[i], fwpos), 'yellow'))
        f.write("%05i %i %g %0.2f %i\n" % (runnumber, fwpos, obs_atten[i],  obs_pe[i],  acquire_time[i]*400))

        if not takedata:
            time.sleep(1)
            continue            
        
            
        if mode == 2 or mode == 3:
            # set delay to pulse generator and look back time (trigger delay) to mimic different block phases
            acquire_data_fast(tm, my_ip, False, tm_id, datafolder, runnumber,acquire_time[i],mode,pg)
        else:
            acquire_data_fast(tm, my_ip, False, tm_id, datafolder, runnumber,acquire_time[i],mode)

    f.close()

    if with_nsbled:
        print(colored("Disabling NSB LED", 'yellow'))
        lc.disable_all()

    control_hv_off(tm)
