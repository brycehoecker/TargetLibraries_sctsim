# Brent Mode
# Created 08 July 2019 to combine functionality for
# generalized prototype TargetC FEE testing.
# Adapted from test_base.py on 12 May 2021 for lab 222
# testing of ramp voltage influence on SNR.

import datetime
# import os
# import sys
import target_driver
import target_io
# import target_calib
import time

import numpy as np

"""
Class for performing generic FEE testing functionality.
This includes functions for initializing the module to doing basic data taking.
"""


class FEETest:
    def __init__(self, data_prefix):
        self.data_prefix = data_prefix
        # Want to time stamp every run only once
        self.today = datetime.datetime.now()
        self.datafile = f"{data_prefix}_{self.today}.fits"
        self.nblocks = None
        self.listener = None
        self.writer = None
        self.buf = None
        self.my_ip = "192.168.12.1"
        self.module_ip = "192.168.12.173"
        self.initialize = True
        self.module_def = ("/Users/brent/svn_folder/TargetDriver/branches"
                           "/issue37423/config"
                           "/SCT_MSA_FPGA_Firmware0xC0000004.def")
        self.asic_def = ("/Users/brent/svn_folder/TargetDriver/branches"
                         "/issue37423/config/TC_ASIC.def")
        self.trigger_asic_def = ("/Users/brent/svn_folder/TargetDriver"
                                 "/branches/issue37423/config/T5TEA_ASIC.def")
        self.module = target_driver.TargetModule(self.module_def,
                                                 self.asic_def,
                                                 self.trigger_asic_def, 0)
        if self.initialize is True:
            time.sleep(0.5)
            self.module.EstablishSlowControlLink(self.my_ip, self.module_ip)
            time.sleep(0.5)
            self.module.Initialise()
            time.sleep(0.5)
            self.module.EnableDLLFeedback()
            print("Module initialized.")
        else:
            self.module.ReconnectToServer(self.my_ip,
                                          8201,
                                          self.module_ip,
                                          8105)

        self.ret, self.fw = self.module.ReadRegister(0)
        print(f"Firmware Version: {self.fw:x}")

    def initialize_module_std(self):
        print("Initializing data taking using "
              "standard parameters and hardsync.")
        self.set_vped()
        self.set_vtrim()
        self.set_comm_params()
        self.start_data_taking()
        self.take_data(duration=15)
        self.stop_data_taking()

    def set_comm_params(self,
                        enable_channels=0xffff,
                        nblocks=8,
                        max_channels=4,
                        trigger_delay=600,
                        tack_trig_type=0b00,
                        tack_trig_mode=0b00):
        for asic in range(4):
            self.module.WriteSetting(f"EnableChannelsASIC{asic}",
                                     enable_channels)

        self.nblocks = nblocks
        # self.module.WriteSetting("Zero_Enable", 0x1)
        self.module.WriteSetting("DoneSignalSpeedUp", 0)
        self.module.WriteSetting("NumberOfBlocks", self.nblocks-1)
        self.module.WriteSetting("MaxChannelsInPacket", max_channels)
        self.module.WriteSetting("TriggerDelay", trigger_delay)
        self.module.WriteSetting("TACK_TriggerType", tack_trig_type)
        self.module.WriteSetting("TACK_TriggerMode", tack_trig_mode)
        for asic in range(4):
            for group in range(4):
                self.module.WriteTriggerASICSetting(f"Wbias_{group}",
                                                    asic,
                                                    985,
                                                    True)
        print(f"Module communications and triggering initialized with "
              f"{nblocks} blocks, {max_channels} max channels per packet, "
              f"{tack_trig_type} trigger type, and {tack_trig_mode} "
              f"trigger mode")

    def set_vped(self, VpedBias=1800, Vped=1200):
        for asic in range(4):
            self.module.WriteTriggerASICSetting("VpedBias",
                                                asic,
                                                VpedBias,
                                                True)
            for channel in range(16):
                self.module.WriteTriggerASICSetting(f"Vped_{channel}",
                                                    asic,
                                                    Vped,
                                                    True)
        time.sleep(1)

    def set_single_vped(self, asic, channel, VpedBias=1800, Vped=1200):
        self.module.WriteTriggerASICSetting("VpedBias",
                                            asic,
                                            VpedBias,
                                            True)
        self.module.WriteTriggerASICSetting(f"Vped_{channel}",
                                            asic,
                                            Vped,
                                            True)
        time.sleep(1)

    def set_vtrim(self):
        for asic in range(4):
            self.module.WriteASICSetting("SSToutFB_Delay",
                                         asic,
                                         58,
                                         True,
                                         False)
            self.module.WriteASICSetting("VtrimT", asic, 1240, True, False)
        time.sleep(1)

    def enable_trigger(self, ext_trig_dir=0x0, tack_enable_trig=0x10000):
        self.module.WriteSetting("ExtTriggerDirection", ext_trig_dir)
        self.module.WriteSetting("TACK_EnableTrigger", tack_enable_trig)

    def disable_trigger(self):
        self.module.WriteSetting("ExtTriggerDirection", 0x0)
        self.module.WriteSetting("TACK_EnableTrigger", 0x0)

    def set_pmtref4_from_file(self):
        dat = np.loadtxt("PMTref4_levels.txt")
        for l in range(4):
            print(dat[l*4, 0], dat[l*4, 2])
            self.module.WriteTriggerASICSetting("PMTref4_0",
                                                int(dat[l*4, 0]),
                                                int(dat[l*4, 2]),
                                                True)
            self.module.WriteTriggerASICSetting("PMTref4_1",
                                                int(dat[l*4, 0]),
                                                int(dat[l*4+1, 2]),
                                                True)
            self.module.WriteTriggerASICSetting("PMTref4_2",
                                                int(dat[l*4, 0]),
                                                int(dat[l*4+2, 2]),
                                                True)
            self.module.WriteTriggerASICSetting("PMTref4_3",
                                                int(dat[l*4, 0]),
                                                int(dat[l*4+3, 2]),
                                                True)
        self.module.WriteSetting("SR_DisableTrigger", 0x1)

    def take_ramp_run(self,
                      ramp,
                      ramp_asic,
                      pack_per_evt=16,
                      buffer_depth=10000,
                      ext_trig_dir=0x0,
                      tack_enable_trig=0x10000,
                      thresh=1000,
                      filename=None,
                      duration=5):
        self.module.WriteASICSetting("Isel", ramp_asic, ramp, True, False)
        self.start_data_taking(pack_per_evt=pack_per_evt,
                               buffer_depth=buffer_depth,
                               ext_trig_dir=ext_trig_dir,
                               tack_enable_trig=tack_enable_trig,
                               thresh=thresh,
                               filename=filename)
        self.data_taking(duration=duration)
        self.stop_data_taking()

    def start_data_taking(self,
                          pack_per_evt=16,
                          buffer_depth=10000,
                          ext_trig_dir=0x0,
                          tack_enable_trig=0x10000,
                          thresh=1500,
                          filename=None):
        time.sleep(5)
        kNPacketsPerEvent = pack_per_evt
        kPacketSize = target_driver.DataPacket_CalculatePacketSizeInBytes(
            4,
            32 * self.nblocks)
        kBufferDepth = buffer_depth
        # for asic in range(4):
        # for group in range(4):
        # self.module.WriteTriggerASICSetting(f"Thresh_{group}",
        #                                     asic, thresh, True)
        if filename is None:
            filename = self.datafile
        self.module.WriteTriggerASICSetting("Thresh_2", 0, thresh, True)
        self.module.WriteSetting("TACK_EnableTrigger", 0)
        self.listener = target_io.DataListener(kBufferDepth,
                                               kNPacketsPerEvent,
                                               kPacketSize)
        self.listener.AddDAQListener(self.my_ip)
        self.listener.StartListening()
        self.writer = target_io.EventFileWriter(filename,
                                                kNPacketsPerEvent,
                                                kPacketSize)
        self.buf = self.listener.GetEventBuffer()
        self.writer.StartWatchingBuffer(self.buf)
        self.module.WriteSetting("ExtTriggerDirection", ext_trig_dir)
        self.module.WriteSetting("TACK_EnableTrigger", tack_enable_trig)
        print(f"Data taking has commenced with external trigger direction "
              f"{ext_trig_dir} and trigger enabled {tack_enable_trig}")

    def stop_data_taking(self):
        self.module.WriteSetting("TACK_EnableTrigger", 0)
        time.sleep(1)
        self.writer.StopWatchingBuffer()
        self.buf.Flush()
        self.writer.Close()
        self.module.CloseSockets()
        self.listener.StopListening()
        del self.listener

    def data_taking(self, duration=5):
        start = time.time()
        while((time.time() - start) < duration):
            print(f"---------Took data for {time.time()-start}s---------")
            ret, temp = self.module.GetTempI2CAux()
            print("Temperatur Aux: {}".format(temp))
            time.sleep(5)

        print("Total Time Elapsed: {}s".format(time.time()-start))

    def efficiency(self, trig_eff_duration):
        self.module.WriteSetting("TriggerEff_Duration", trig_eff_duration)
        _, done_bit = self.module.ReadSetting("TriggerEff_DoneBit")
        time.sleep(0.1)
        while done_bit == 0:
            _, done_bit = self.module.ReadSetting("TriggerEff_DoneBit")
        _, n = self.module.ReadSetting("TriggEffCounter")
        print(n)
        return n

    def single_trigger_pixel_thresh_scan(self,
                                         asic,
                                         group,
                                         trigger_duration,
                                         thresh_start=1000,
                                         thresh_stop=2000,
                                         step=20):
        filename = f"{self.data_prefix}_{self.today}.txt"
        trig_eff_duration = int(trigger_duration / 8. * 1.0e9)
        self.module.WriteSetting("TriggerEff_Enable", 2 ** (asic * 4 + group))
        with open(filename, "w") as f:
            f.write("Thresh,Rate")
            for i, thresh in enumerate(range(thresh_start, thresh_stop, step)):
                thresh_name = f"Thresh_{int(group)}"
                self.module.WriteTriggerASICSetting(thresh_name,
                                                    int(asic),
                                                    thresh,
                                                    True)
                time.sleep(0.01)
                counts = self.efficiency(trig_eff_duration)
                rate = float(counts) / trigger_duration  # rate in Hz
                print(f"Group: {group}, Thresh: {thresh}, Counts: {counts}, "
                      f"Rate (Hz): {rate}")
                f.write(f"{thresh},{rate}\n")


if __name__ == "__main__":
    print("Testing script functionality!")
    test = FEETest()
    test.initialize_module_std()
