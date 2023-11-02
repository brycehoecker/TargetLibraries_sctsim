# -*- coding: utf-8 -*-
"""
TARGET Module Gain Matching Functions for MPIK
     originally from Steve Leach (UoL) - adapted by Justus Zorn (MPIK) -- Sep2018

"""
version = '***'

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import os
import sys
import time
import target_driver
import target_io
from astropy.io import fits
import matplotlib.pyplot as plt
from CHECLabPy.core.io import DL1Reader
from CHECLabPy.plotting.camera import CameraImage, CameraImageImshow

sys.path.append('/home/cta/MPIKLabSoftware/FilterWheel/')
import FilterWheel

global nmaxchan, nblocks
nmaxchan = 1
nblocks = 4


###########################################################################################
def setup_tm(my_ip='192.168.12.1', tm_ip='192.168.12.175', delay=300):
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
    tm.WriteSetting("TriggerDelay",
                    triggerdelay)  # lookback time between instant when the trigger is issued and the portion of the ASIC storage to digitize

    return tm


###########################################################################################
def control_hv_on(tm, HV_calib):
    for i in range(16):
        tm.SetHVDAC(i, HV_calib[i])  # superpixel 0 to 15
    print("Turn on HV and let settle.....\n")
    tm.EnableHVAll()
    time.sleep(2)  # wait
    print("HV current", tm.ReadHVCurrentInput())


### ########################################################################################
def control_hv_off(tm):
    tm.DisableHVAll()


###########################################################################################
def acquire_data_fast(tm, my_ip, tm_id, take_PED, datafolder):
    if take_PED:
        datafile = 'data_0_0_PED.tio'
        acquire_time = 60  # 30
    else:
        datafile = 'data_0_0_r0.tio'
        acquire_time = 2

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
    tm.WriteSetting("TACK_EnableTrigger", 0x10000)  #
    # tm.WriteSetting("TACK_EnableTrigger", 0b000110000111001011)  # waveform trigger group (values ****)

    time.sleep(acquire_time)  # wait to accumulatedata

    ######### Stop data taking ###################
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
        os_command = "/home/cta/Software/TargetCalib/install/./apply_calibration -i {0} -p {1}/data_0_0_ped.tcal -t /home/cta/CHECDevelopment/CHECS/Operation/{2}_tf.tcal".format(
            datafolder + datafile, datafolder, tm_id)
        os.system(os_command)
        # read_data_fast()


###########################################################################################
def match_gain(tm, my_ip, gain_match_loops, gain_required, datafolder, tm_id, take_PED=False):
    global HV_calib, amp_pulse_channel_mean
    datafile = 'data_0_0_r1.tio'

    GAIN_CALIB = 14.3  # mV/DAC
    DAC_level = 0
    HV_DAC_DEFAULT = 50

    ######Take PED and generate calibration file
    control_hv_off(tm)
    print('\nTurned off HV, wait for it to settle........\n')
    time.sleep(5)
    print('\nTaking PED file........\n')
    if take_PED:
        acquire_data_fast(tm, my_ip, tm_id, take_PED, datafolder)

    ###### Acquire fast data
    HV_calib = [(DAC_level) for i in range(16)]

    broken_pix_list = np.zeros(64)

    for j in range(gain_match_loops):
        print(HV_calib)
        control_hv_on(tm, HV_calib)
        time.sleep(6)
        acquire_data_fast(tm, my_ip, tm_id, False, datafolder)
        print('\n************ Step', j + 1, 'of', gain_match_loops, gain_required,
              'mV gain matching data acquired, processing........\n')

        extract_data(tm_id, datafolder, j, gain_required)
        cut = 0
        if j > 3: cut = gain_required * 0.1  # 0.1
        if j > 6: cut = gain_required * 0.2  # 0.2
        if j > 9: cut = gain_required * 0.3

        #from IPython import embed
        #embed()

        amp_pulse_channel_mean = np.ma.masked_where(amp_pulse_channel_mean < cut,amp_pulse_channel_mean)
        broken_pix_list += (amp_pulse_channel_mean.mask==True)
        print(broken_pix_list)

        for i in range(16):
            SP_amp = np.mean(amp_pulse_channel_mean[i * 4:(i + 1) * 4])
            DAC_change = int((SP_amp - gain_required) / GAIN_CALIB)
            HV_new = HV_calib[i] + DAC_change
            if HV_new + HV_DAC_DEFAULT < 0:
                HV_new = 0 - HV_DAC_DEFAULT
            elif HV_new + HV_DAC_DEFAULT > 254:
                HV_new = 254 - HV_DAC_DEFAULT
            print('\nSP', i, '\tPrev DAC:', HV_calib[i], '\tDAC change:', DAC_change, '\tNew DAC:', HV_new)
            HV_calib[i] = HV_new

        time.sleep(1)

    print('\n************ Gain matching complete\nSee file hvSetting_gainmatched_SN****_***mV.cfg\n')
    hv_config = open(datafolder + "hvSetting_gainmatched_{0}_{1}mV.cfg".format(tm_id, int(gain_required)), 'w')
    for i in range(16):
        hv_config.write('{0}'.format(int(HV_calib[i])))
        if i < 15:
            hv_config.write(', ')
        elif i == 15:
            hv_config.write('\n')
    hv_config.close()


###########################################################################################
def extract_data(tm_id, datafolder, count=0, gain=0):
    global amp_pulse_pixel_mean, amp_pulse_channel_mean
    datafile = "data_0_0_r1.tio"
    os_command = "python /home/cta/Software/CHECLabPy/scripts/extract_dl1.py -f {0}".format(datafolder + datafile)
    os.system(os_command)

    amp_pulse_pixel_mean = np.zeros(64)
    amp_pulse_channel_mean = np.zeros(64)
    with DL1Reader(datafolder + 'data_0_0_dl1.h5') as reader:
        pixel_arr, amp_pulse = reader.select_columns(['pixel', 'amp_pulse'])
    for i in range(64):
        amp_pulse_channel_mean[i] = np.mean(amp_pulse[pixel_arr == i])
        amp_pulse_pixel_mean[i] = amp_pulse_channel_mean[i]
        # int(np.argwhere(lut_channel == pixel))
        # int(lut_channel[fast_pixel-1])
        print('pixel', i, 'mean', amp_pulse_pixel_mean[i])

    mean = np.mean(amp_pulse_pixel_mean)
    minimum = np.min(amp_pulse_pixel_mean)
    maximum = np.max(amp_pulse_pixel_mean)
    events = int(amp_pulse.size / 64)

    spread = (maximum - minimum) / mean * 100
    print('\nEvents:', events, '\nMean amplitude:', mean, '\tstd:', np.std(amp_pulse_pixel_mean))
    print('Min amplitude:', minimum, '\tMax: ', maximum)
    print('% Spread:', spread, '\n')

    output_data = open(datafolder + 'data_0_0_r0_runlog.txt', 'w')
    output_data.write('TM :{0}\n'.format(tm_id))
    output_data.write(
        'Events: {0}\nMean: {1}\nMin: {2}\nMax: {3}\nSpread: {4}\n\n'.format(events, mean, minimum, maximum, spread))
    for i in range(64):
        output_data.write('p{0}\t{1}\n'.format(i + 1, round(amp_pulse_pixel_mean[i], 1)))
    output_data.close()

    # np.savetxt(datafolder+'test_file.txt', mean, minimum, maximum, spread)
    reader = DL1Reader(datafolder + 'data_0_0_dl1.h5')
    camera = CameraImage.from_mapping(reader.mapping)
    if gain == 0:
        maxlimit = int(np.max(amp_pulse_pixel_mean))
    else:
        maxlimit = int(gain * 1.5)
    camera.add_colorbar("Amplitude (mV)")

    camera.image = amp_pulse_pixel_mean
    plot_filename = 'data_tile_plot_autoscale_{0}.png'.format(count)
    plt.savefig(datafolder + plot_filename)

    camera.set_limits_minmax(0, maxlimit)
    plot_filename = 'data_tile_plot_{0}.png'.format(count)
    plt.savefig(datafolder + plot_filename)

    plt.clf()
    print('\nPlotting tile images, see:', datafolder + plot_filename, '\n')


if __name__ == "__main__":
    fw_ip = "192.168.0.215"
    fw_pe = 50

    datafolder = "/home/cta/UserSpace/Justus/d2018-09-19-SingleTM-gainmatching/200mV/"

    fw = FilterWheel.FilterWheel(ip=fw_ip)
    fw.initialise()
    fw.move(pe=fw_pe, pe_calib=0.1)

    my_ip = '192.168.12.1'
    tm = setup_tm(my_ip=my_ip, tm_ip='192.168.12.126', delay=345)

    loops = 11
    goal_amplitude = 200
    tm_id = "SN0041"
    take_ped = True

    match_gain(tm, my_ip, loops, goal_amplitude, datafolder, tm_id, take_ped)
    #
    #
    #
    #
    # des = "Perform gain matching based on a target mean pulse height " \
    #       "and changing DAC according to a reference formula" \
    #       "Take gain matching data: \n" \
    #       "python camera_gainmatching_itterate.py --mode 2 --ntry 10 --target 200 --fw_pe 50 " \
    #       "--out " \
    #       "/home/cta/CHECDevelopment/CHECS/TestResults/GainMatching/itterative/d2018-03-15_200mV_fw50pe.cfg"\
    #       "Make plots: \n" \
    #       "python camera_gainmatching_itterate.py --mode 3 " \
    #        "--out /home/cta/CHECDevelopment/CHECS/TestResults/GainMatching/itterative/d2018-03-15_200mV_fw50pe.cfg"
    # parser = argparse.ArgumentParser(description=des)
    # parser.add_argument("--out", type=str, help="Resulting HV file name", default="gainmatched.cfg")
    # parser.add_argument("--r1", type=str, help="R1 file to analyse (mode==1)", default=None)
    # parser.add_argument("--arc", type=str, help="Archive directory", default=def_arc)
    # parser.add_argument("--arc_mode", type=int, help="- 1:\tDon't touch the data\n" \
    #                     "- 2:\tMove data to archive (default)" \
    #                     "- 3:\tDelete the data", default=2)
    # parser.add_argument("--hv", type=str, help="- HV file used to take r1 data (mode 1) \n" \
    #                                            "- HV file name to start from (mode == 2, optional)", default=None)
    # parser.add_argument("--obs", type=str, help="Observing file name (mode == 2)", default=def_obs)
    # parser.add_argument("--obsped", type=str, help="Observing file name for pedestal (mode == 2)", default=def_obsped)
    # parser.add_argument("--ped", type=str,
    #                     help="Pedestal (tcal) file name - if not specified then will be created (mode == 2)",
    #                     default=None)
    # parser.add_argument("--ntry", type=int, help="Number of itterations (mode == 2), default: 1", default=1)
    # parser.add_argument("--target", type=int, help="Goal pulse height (mV), default: 800", default=800)
    # parser.add_argument("--fw_pe", type=int, help="Filter wheel pe setting, default: 50", default=50)
    # parser.add_argument("--fw_ip", type=str, help="Filter wheel IP, default: 192.168.0.215", default="192.168.0.215")
    # parser.add_argument("--pg_name", type=str, help="Pulse generator name, default: /dev/ttyUSB0", default="/dev/ttyUSB0")
    # parser.add_argument("--laser_delay", type=int, help="Time in ns laser trigger signal should be delayed with respect to backplane trigger, default: 410", default=410)
    # # Need to add relationship between target mV and FW setting...
    #
    # args = parser.parse_args()
    #
    # # Should run some checks on the arguments...
    # flog_name = args.log
    # fobs_name = args.obs
    # fobsped_name = args.obsped
    # mode = args.mode
    # ntry = args.ntry
    # fhv_name = args.hv
    # fres_name = args.out
    # target = args.target
    # fw_pe = args.fw_pe
    # fw_ip = args.fw_ip
    # pg_name = args.pg_name
    # fr1_name = args.r1
    # fped_name = args.ped
    # laser_delay = args.laser_delay
    # arc_mode = args.arc_mode
    # slow = args.slow
