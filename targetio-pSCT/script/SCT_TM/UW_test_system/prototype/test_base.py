# Brent Mode
# Created 08 July 2019 to combine functionality for generalized prototype TargetC FEE testing.

from __future__ import print_function

from Agilent33600A import Agilent33600A as func_gen
import datetime
import logger
import os
import powerCycle
import sys
import target_driver
import target_io
import target_calib
import time

"""Class for performing generic FEE testing functionality. This includes functions for initializing the module to doing basic data taking."""
class FEETest(object):
    def __init__(self, args):
        self.args = args # This is set up so that it expects command line arguments to be passed that consist of Signal Type, Period, High, Low, Module serial number, and the Testing Requirement
        self.today = datetime.datetime.now() # Want to time stamp every run only once

        self.bps = powerCycle.powerCycle()

        self.nblocks = None
        self.fg = None
        self.listener = None
        self.writer = None
        self.buf = None

        # This control statement should implement interactive logging if not all command line arguments are given for the run
        if len(args) == 8:
            self.args.pop(0)
        else:
            self.args = []
            self.args.append(str(raw_input("Signal Type (sin, pulse, or noise): ")))
            self.args.append(float(raw_input("Signal Period (ns): ")))
            self.args.append(float(raw_input("Pulse Width (ns) (0 if sin or noise): ")))
            self.args.append(float(raw_input("Signal Amplitude (mV): ")))
            self.args.append(float(raw_input("Signal Offset (mV): ")))
            self.args.append(int(raw_input("Module SN: ")))
            self.args.append(str(raw_input("FEE Testing Requirement (choose from document or input 'None'): ")))

        self.signal = self.args[0]
        self.period = self.args[1]
        self.width = self.args[2]
        self.ampl = self.args[3]
        self.offset = self.args[4]

        self.datafile = logger.log(self.today, self.args[0], self.args[1], self.args[2], self.args[3], self.args[4], self.args[5], self.args[6])
        print(self.datafile)
        # Below is the initialization process taken from tkdata_generic, which itself is taken from the takedata2018.py script that we received from INFN
        self.my_ip = "192.168.12.1"
        self.module_ip = "192.168.12.173"
        self.initialize = True
        self.module_def = "/Users/brent/TargetDriver_issue37423/config/SCT_MSA_FPGA_Firmware0xC0000001.def"
        self.asic_def = "/Users/brent/TargetDriver_issue37423/config/TC_ASIC.def"
        self.trigger_asic_def = "/Users/brent/TargetDriver_issue37423/config/T5TEA_ASIC.def"
        self.module = target_driver.TargetModule(self.module_def, self.asic_def, self.trigger_asic_def, 0)
        if self.initialize is True:
            self.module.EstablishSlowControlLink(self.my_ip, self.module_ip)
            self.module.Initialise()
            self.module.EnableDLLFeedback()
            print("Module initialized.")
        else:
            module.ReconnectToServer(self.my_ip, 8201, self.module_ip, 8105)

        self.ret, self.fw = self.module.ReadRegister(0)
        print("Firmware Version: {:x}".format(self.fw))

    def initialize_module_std(self):
        print("Initializing data taking using standard parameters and hardsync.")
        self.set_vped()
        self.set_vtrim()
        self.set_comm_params()
        self.start_data_taking()
        self.take_data(time=15)
        self.stop_data_taking()


    def set_comm_params(self, enable_channels=0xffff, nblocks=8, max_channels=4, trigger_delay=500, tack_trig_type=0x0, tack_trig_mode=0x0):
        for asic in range(4):
            self.module.WriteSetting("EnableChannelsASIC{}".format(enable_channels))

        self.nblocks = nblocks
        self.module.WriteSetting("Zero_Enable", 0x1)
        self.module.WriteSetting("DoneSignalSpeedup", 0)
        self.module.WriteSetting("NumberOfBlocks", self.nblocks-1)
        self.module.WriteSetting("MaxChannelsInPacket", max_channels)
        self.module.WriteSetting("TriggerDelay", trigger_delay)
        self.module.WriteSetting("TACK_TriggerType", tack_trig_type)
        self.module.WriteSetting("TACK_TriggerMode", tack_trig_mode)
        print("Module communications and triggering initialized with {} blocks, {} max channels per packet, {} trigger type,\
                and {} trigger mode".format(nblocks, max_channels, tack_trig_type, tack_trig_mode))

    def set_func_gen(self):
        exception = None
        self.fg = None
        try:
            self.fg = func_gen()
            if self.signal == 'pulse':
                self.fg.apply_pulse(self.freq, self.ampl, self.offset)
            elif self.signal == 'sin':
                self.fg.apply_sin(self.freq, self.ampl, self.offset)
            elif self.signal == 'noise':
                pass
            else:
                print("Look, none of those were valid, you've mucked up the log, I guess we're taking pedestal data now.")
                pass
        except:
            exception = sys.exc_info()

        if exception:
            self.stop_data_taking()
            time.sleep(1)
            raise SystemExit

    def set_vped(self, VpedBias=1800, Vped=1200):
        for asic in range(4):
            self.module.WriteTriggerASICSetting("VpedBias", asic, VpedBias, True)
            for channel in range(16):
                self.module.WriteTriggerASICSetting("Vped_{}".format(channel), channel, Vped, True)
        time.sleep(1)

    def set_vtrim(self):
        for asic in range(4):
            self.module.WriteASICSetting("SSToutFB_Delay", asic, 58, True, False)
            self.module.WriteASICSetting("VtrimT", asic, 1240, True, False)
        time.sleep(1)

    def start_data_taking(self, pack_per_evt=16, buffer_depth=10000, ext_trig_dir=0x1, tack_enable_trig=0x10000):
        kNPacketsPerEvent = pack_per_evt
        kPacketSize = target_driver.DataPacket_CalculatePacketSizeInBytes(4, 32 * self.nblocks)
        kBufferDepth = buffer_depth
        self.listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
        self.listener.AddDAQListener(self.my_ip)
        self.listener.StartListening()
        self.writer = target_io.EventFileWriter(self.datafile, kNPacketsPerEvent, kPacketSize)
        self.buf = self.listener.GetEventBuffer()
        self.set_fun_gen()
        self.writer.StartWatchingBuffer(self.buf)
        self.module.WriteSetting("ExtTriggerDirection", ext_trig_dir)
        self.module.WriteSetting("TACK_EnableTrigger", tack_enable_trig)
        print("Data taking has commenced with external trigger direction {} and trigger enabled {}".format(ext_trig_dir, tack_enable_trig))

    def stop_data_taking(self):
        self.module.WriteSetting("TACK_EnableTrigger", 0)
        time.sleep(1)
        self.writer.StopWatchingBuffer()
        self.module.CloseSockets()
        self.buf.Flush()
        self.writer.Close()
        if self.fg:
            self.fg.close()
        else:
            pass
        powerCycle.powerOff(self.bps)

    def take_data(self, time=5):
        start = time.time()
        while((time.time() - start) < time):
            print("---------Took data for {}s---------".format(time.time()-start))
            ret, temp = self.module.GetTempI2CAux()
            print("Temperatur Aux: {}".format(temp))
            time.sleep(5)

        print("Total Time Elapsed: {}s".format(time.time()-start))


if __name__ == "__main__":
    print("Testing script functionality!")
    test = FEETest(sys.argv)
    test.initialize_module_std()
