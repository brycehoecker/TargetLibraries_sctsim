import target_driver
import target_io
import target_calib
import time
from astropy.io import ascii
import os
import sys
import argparse
from tqdm import tqdm
import numpy as np
import yaml
from MyLogging import logger
from utils import *
from agilent33250A_inverted import *
import enlighten
from arduino_utils import *
import datetime
#import gc

class TCModule:
    def __init__(self, my_ip = "192.168.12.3", module_ip = "192.168.12.173",
                 module_def="/home/target5/SCT_MSA_FPGA_Firmware0xC0000004.def",
                 asic_def = "/home/target5/Software/TargetDriver/trunk/config/TC_ASIC.def",
                 trigger_asic_def = "/home/target5/Software/TargetDriver/trunk/config/T5TEA_ASIC.def",
                 reset=True, smart=True):
        self.myinfo = MyInfo()
        self.nasic = 4
        self.ntrig_group = 4 ## trigger group per asic
        self.nch = 16 ##channel per asic
        self.total_blocks = 512 #128 # max is 512, but working with reduced buffer
        #self.module_def = "/home/target5/SCT_MSA_FPGA_Firmware0xC0000006.def"
        #self.module_def = "/home/target5/SCT_MSA_FPGA_Firmware0xC0000005.def"
        self.module_def = "/home/target5/SCT_MSA_FPGA_Firmware0xC0000004.def"
        #self.module_def = "/home/target5/Software/TargetDriver/trunk/config/SCT_MSA_FPGA_Firmware0xC0000001.def"
        #self.module_def = "/home/target5/Software/TargetDriver/branches/issue37423/config/SCT_MSA_FPGA_Firmware0xC0000004.def"
        self.asic_def = "/home/target5/Software/TargetDriver/trunk/config/TC_ASIC.def"
        self.trigger_asic_def = "/home/target5/Software/TargetDriver/trunk/config/T5TEA_ASIC.def"
        self.module_def = "/home/leonardo/Software/TARGET/firmware_smart/SCT_MSA_FPGA_Firmware0xC0000009.def"
        self.asic_def = "/home/leonardo/Software/TARGET/TargetDriver/trunk/config/TC_ASIC.def"
        self.trigger_asic_def = "/home/leonardo/Software/TARGET/TargetDriver/trunk/config/T5TEA_ASIC.def"
        self.my_ip = my_ip
        self.module_ip = module_ip
        self.module_def = module_def
        self.asic_def = asic_def
        self.trigger_asic_def = trigger_asic_def
        self.module = target_driver.TargetModule(self.module_def, self.asic_def, self.trigger_asic_def, 0)
        if not reset:
            #try:
            ret = self.module.ReconnectToServer(my_ip, 8201, module_ip, 8105)
            if ret==-1:
                raise Exception("Reconnection to module failed.")
            else:
                logger.info("Reconnection to module successful (" + str(ret) + ")")
        else:
            ret = self.module.EstablishSlowControlLink(my_ip, module_ip)
            self.module.Initialise()
            self.module.EnableDLLFeedback()
            if ret==0 or ret==3:
                logger.info ("Module initialization successful (" + str(ret) + ")")
            else:
                msg = "Could not establish connection. Connection code: (" + str(ret) + ")"
                logger.log(logger.TEST_LEVEL_FAIL,msg) 
                raise Exception(msg)

        ret, fw = self.module.ReadRegister(0)
        logger.info ("Firmware version: {:x}".format(fw))
        self.fw_version = fw
        if smart:
            self.module.WriteSetting("SMART_SPI_Enable", 0x1)
        else:
            self.module.WriteSetting("SMART_SPI_Enable", 0x0)
            
        self.module.WriteSetting("TACK_EnableTrigger", 0)   # disable all triggers
        self.triggermask = 0x0 ## trigger mask, default is 0 -> disable triggers; set 0x10000 for hardware trigger; set 0xffff for all groups
        #######self.module.DisableHVAll() #disable all for safety, atm turn on by default
        self.temp1, self.temp2, self.temp3, self.temp4 = -1., -1., -1., -1.

        self.tbob, self.sbob1, self.sbob2 = None, None, None
        if True:
            self.load_arduinos()

    ### setup arduinos
    def load_arduinos(self):
        ## TBOB
        self.tbob = ArduinoTBOB(ard_id="TBOB")
        if not self.tbob.is_open:
            logger.warning("Could not load arduino on trigger board. Tests will be done without it.")
            self.tbob = None

        #reset the trigger mux to group0 (which is in OR with external trigger)
        self.reset_tbob_mux()

        ## SBOBs
        self.sbob1 = ArduinoSBOB(ard_id="BOB1")
        if not self.sbob1.is_open:
            logger.warning("Could not load arduino on signal breakout board. Tests will be done without it.")
            self.sbob1 = None
        self.sbob2 = ArduinoSBOB(ard_id="BOB2")
        if not self.sbob2.is_open:
            logger.warning("Could not load arduino on signal breakout board. Tests will be done without it.")
            self.sbob2 = None

    def reset_tbob_mux(self):
        if self.tbob:
            self.tbob.setmux(0)
        else:
            logger.warning("No arduino on trigger board loaded. Could not set trigger group. Nothing done.")
            #logger.error("No arduino on trigger board loaded. Could not set trigger group. Nothing done.")
            #raise Exception("Error while setting trigger MUX")
        
    
    def set_Vpeds(self, vped_file=None, vpedbias = 1800, vped=1200):
        ### Setting VPEDs ###
        if vped_file is not None:
            raise NotImplementedError("config from file not implemented")
            with open(VPED_FILE) as f:
                content = f.readlines()
                content = [x.strip() for x in content]
        else:
            content = np.ones(64)*vped

        logger.info("Setting VPEDs to")
        for asic in range(self.nasic):
            ret = self.module.WriteTriggerASICSetting("VpedBias", asic, vpedbias, True)
            for channel in range(self.nch):
                logger.info(str(asic) + "   " + str(channel) + "   " + str(asic*16+channel) + "   " + str(content[asic*16+channel]))
                self.module.WriteTriggerASICSetting("Vped_{}".format(channel), asic, int(content[asic*16+channel]), True)
                #logger.info(str(asic) + "   " + str(channel) + "   " + str(asic*16+channel) + "   " + str(vped))
                #self.module.WriteTriggerASICSetting("Vped_{}".format(channel), asic, int(vped), True)
        time.sleep(1)

    def set_SSToutFB_Vtrim(self, vtrim_file=None, vtrim=1240, sstoutfb=58):
        ### Setting optimized SSToutFB and VtrimT ###
        if vtrim_file is not None:
            raise NotImplementedError("config from file not implemented")
            data = ascii.read(vtrim_file)
            #logger.info(data)
        else:
            data = None

        for asic in range(self.nasic):
            #logger.info("Setting SSToutFB_Delay of Asic " + str(asic) + " to " + str(int(data[asic][2])))
            #module.WriteASICSetting("SSToutFB_Delay", asic, int(data[asic][2]), True, False) # standard value: 58
            #logger.info("Setting VtrimT of Asic " + str(asic) + " to " + str(int(data[asic+4][2])))
            #module.WriteASICSetting("VtrimT", asic, int(data[asic+4][2]), True, False) # standard value: 1240
            logger.info("Setting SSToutFB_Delay of Asic " + str(asic) + " to " + str(sstoutfb))
            self.module.WriteASICSetting("SSToutFB_Delay", asic, int(sstoutfb), True, False) # standard value: 58
            logger.info("Setting VtrimT of Asic " + str(asic) + " to " + str(vtrim))
            self.module.WriteASICSetting("VtrimT", asic, int(vtrim), True, False) # standard value: 1240
        time.sleep(1)

    def set_trigger_params(self, wbias=None, pmtref4=None, thresh=None, gain=None):
        ### Setting trigger parameters ###
        ## add possibility to avoid setting one parameter by passing None
        if wbias is not None and not hasattr(wbias,'__iter__'):
            wbias = np.array([wbias]*self.nasic*self.ntrig_group).reshape((self.nasic,self.ntrig_group))
        if pmtref4 is not None and not hasattr(pmtref4,'__iter__'):
            pmtref4 = np.array([pmtref4]*self.nasic*self.ntrig_group).reshape((self.nasic,self.ntrig_group))
        if thresh is not None and not hasattr(thresh,'__iter__'):
            thresh = np.array([thresh]*self.nasic*self.ntrig_group).reshape((self.nasic,self.ntrig_group))
        if gain is not None and not hasattr(gain,'__iter__'):
            gain = np.array([gain]*self.nasic*self.nch).reshape((self.nasic,self.nch))

        for asic in range(self.nasic):
            for group in range(self.ntrig_group):
                if wbias is not None:
                    self.module.WriteTriggerASICSetting("Wbias_"+str(group), asic, int(wbias[asic][group]), True)
                if pmtref4 is not None:
                    self.module.WriteTriggerASICSetting("PMTref4_"+str(group), asic, int(pmtref4[asic][group]), True)
                    logger.info("set_trigger_params--> setting pmtref group " + str(asic*4+group) + " to " + str(int(pmtref4[asic][group])))
                if thresh is not None:
                    self.module.WriteTriggerASICSetting("Thresh_"+str(group), asic,int(thresh[asic][group]), True)
                    logger.info("set_trigger_params--> setting thresh group " + str(asic*4+group) + " to " + str(int(thresh[asic][group])))
            for ch in range(self.nch):
                if gain is not None:
                    self.module.WriteTriggerASICSetting("TriggerGain_Ch"+str(ch), asic, int(gain[asic][ch]), True)
                    self.module.WriteTriggerASICSetting("TriggerEnable_Ch"+str(ch), asic, 0x1, True)
        time.sleep(1)

    def read_temperatures(self):
        self.temp1, self.temp2, self.temp3, self.temp4 = -1., -1., -1., -1.
        ret,self.temp1 =  self.module.GetTempI2CPrimary()
        logger.info ("Temperature Pri: " + str(self.temp1))
        ret, self.temp2 =  self.module.GetTempI2CAux()
        logger.info ("Temperature Aux: " + str(self.temp2))
        #ret, self.temp3 =  self.module.GetTempI2CPower()
        #print ("Temperature Pow: ",self.temp3)
        #ret, self.temp4 =  self.module.GetTempSIPM()
        #print ("Temperature Camera: {:3.2f}".format(self.temp4))
        return self.temp1, self.temp2, self.temp3, self.temp4

    def read_hv(self):
        time.sleep(0.01)
        ret, current = self.module.ReadHVCurrentInput()
        correction_factor = 10.0 #currently, the FW is expecting 1 ohm resistor shunt, but we are using 0.1 ohm 1%...
        current_amps = current*correction_factor
        logger.info ("LTC4151, HV current (Amperes, not calibrated): " + str(current_amps))
        time.sleep(0.01)
        ret, voltage = self.module.ReadHVVoltageInput()
        logger.info ("LTC4151, HV voltage (before regulator, Volts): " + str(voltage))
        return current_amps, voltage




    def prepare_daq(self, asics=None, nblocks = 4, triggerdelay=500, packet_event=4, triggertype=1, triggermask=0xffff, pmtref4=2000, thresh=2000,warmup_time=60):
        """If asics=None enable all asics, otherwise provide a list with asics to enable [0,1,2,3]
        triggertype=0 -> inttrigger, triggertype=1 -> exttrigger, triggertype=2 -> hardsync
        warmup_time in seconds. if 0 or negative, no warmup is done
        """
        self.myinfo["nblocks"] = nblocks
        self.myinfo["packet_event"] = packet_event
        self.myinfo["trigger_delay"] = triggerdelay
        if asics is None:
            asics = range(self.nasic)

        for asic in range(self.nasic):
            if asic in asics:
                self.module.WriteSetting("EnableChannelsASIC{}".format(asic), 0xffff)
            else:
                self.module.WriteSetting("EnableChannelsASIC{}".format(asic), 0x0)

        self.nblocks = nblocks
        self.kMaxChannelInPacket = int( 64/packet_event )
        self.kNPacketsPerEvent = packet_event
        self.kPacketSize = target_driver.DataPacket_CalculatePacketSizeInBytes( self.kMaxChannelInPacket, 32 * (self.nblocks))
        self.kBufferDepth = 10000
        self.module.WriteSetting("Zero_Enable", 0x0)
        self.module.WriteSetting("DoneSignalSpeedUp",0)
        self.module.WriteSetting("NumberOfBlocks", nblocks-1)
        self.module.WriteSetting("MaxChannelsInPacket", self.kMaxChannelInPacket)

        self.module.WriteSetting("TriggerDelay", int(triggerdelay) ) # lookback time between instant when the trigger is issued and the portion of the ASIC storage to digitize
        self.module.WriteSetting("TACK_TriggerType", 0x0)
        self.module.WriteSetting("TACK_TriggerMode", 0x0)
        #self.module.WriteSetting("SlowADCEnable_Power",1)
        #################### TEST PEDESTAL SUBTRACTION ISSUE
        #self.module.WriteSetting("RCLR_FINISH",6400) ## just for testing
        
        if triggertype==2 :
            self.myinfo["trigger_type"] = "hardsync"
            logger.info("setting hardsync trigger")
            self.module.WriteSetting("ExtTriggerDirection", 0x1) # hardsync
            self.triggermask = 0x10000
        elif triggertype==1 :
            self.myinfo["trigger_type"] = "external"
            self.module.WriteSetting("ExtTriggerDirection", 0x0) # external
            self.triggermask = 0x10000
        elif triggertype==0 :
            self.myinfo["trigger_type"] = "internal"
            self.myinfo["trigger_mask"] = triggermask
            self.module.WriteSetting("ExtTriggerDirection", 0x1) # hardsync
            self.triggermask = triggermask # 0xffff
        else :
            raise ValueError("Wrong trigger type.")

        if triggertype==0:
            logger.info("setting trigger params")
            self.set_trigger_params(wbias=985, pmtref4=pmtref4, thresh=thresh, gain=0x15)

        if warmup_time>0:
            logger.info("Waiting "+str(warmup_time)+" seconds to stabilise")
            self.module.WriteSetting("TACK_EnableTrigger", 0x10000)
            manager = enlighten.get_manager()
            pbar = manager.counter(total=int(warmup_time), desc='DAQ warmup', leave = False)

            for i in range(1, int(warmup_time)+1):
               #logger.info("Processing step %s" % i)
               time.sleep(1)
               pbar.update()

            self.module.WriteSetting("TACK_EnableTrigger", 0)
            time.sleep(1.)
            pbar.close()
            manager.stop()


    def daq(self, outfile, daq_time=1, delay_loop=False, check_pkts=True): # daq_time in seconds, when delay loop is true daq time is for each delay
        # by default we have a data packet for each channel, this can be changed
        listener = target_io.DataListener(self.kBufferDepth, self.kNPacketsPerEvent, self.kPacketSize)
        listener.AddDAQListener(self.my_ip)
        listener.StartListening()
        writer = target_io.EventFileWriter(outfile, self.kNPacketsPerEvent, self.kPacketSize)
        buf = listener.GetEventBuffer()
        writer.StartWatchingBuffer(buf)




        #logger.log(logger.TEST_LEVEL_INFO, "Start datataking...")
        ####start data taking
        if delay_loop :
            manager = enlighten.get_manager()
            total = self.total_blocks*2;
            pbar = manager.counter(total=total, desc='Pedestal delay scan (hardsync)', leave = False)

            offset = 27 # this depends on the firmware, 26 is ok for C0005, C0008, C000B, 27 is ok for C0004_4, C0009, C000A
            if self.fw_version in [0xc0000005, 0xc0000008, 0xc000000b]:
                offset = 26
            elif self.fw_version in [0xc0000004, 0xc0000009, 0xc000000a, 0xc000000C]:
                offset = 27
            for i in range(0,self.total_blocks):
                self.module.WriteSetting("TriggerDelay", i*32+offset)
                #if (i % 50 == 0): logger.log(logger.TEST_LEVEL_INFO, "------ Taking hardsync data with delay of {} ns -------".format(i*32+offset))
                #else:
                logger.info("------ Taking hardsync data with delay of {} ns -------".format(i*32+offset))
                self.read_temperatures()
                #self.module.WriteSetting("TACK_EnableTrigger", 0x10000)  # hardware trigger
                self.module.WriteSetting("TACK_EnableTrigger", self.triggermask)
                time.sleep(daq_time) # wait some time to accumulate data
                self.module.WriteSetting("TACK_EnableTrigger", 0)
                pbar.update()
            
            for i in range(0,self.total_blocks): # scan again with 1 cell shift
                self.module.WriteSetting("TriggerDelay", i*32+offset+1)
                #if (i % 50 == 0): logger.log(logger.TEST_LEVEL_INFO, "------ Taking hardsync data with delay of {} ns -------".format(i*32+offset+1))
                #else:
                logger.info("------ Taking hardsync data with delay of {} ns -------".format(i*32+offset+1))
                self.read_temperatures()
                #self.module.WriteSetting("TACK_EnableTrigger", 0x10000)  # hardware trigger
                self.module.WriteSetting("TACK_EnableTrigger", self.triggermask)
                time.sleep(daq_time) # wait some time to accumulate data
                self.module.WriteSetting("TACK_EnableTrigger", 0)   # disable all triggers
                pbar.update()


            pbar.close()
            manager.stop()
            
        else:
            #self.module.WriteSetting("TACK_EnableTrigger", 0x10000)
            self.module.WriteSetting("TACK_EnableTrigger", self.triggermask)
            #time.sleep(daq_time) # wait some time to accumulate data
            self.waitloop_datataking(daq_time)
            self.module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers

        time.sleep(1)
        ####close connection to module and output file
        writer.StopWatchingBuffer()  # stops data storing in file
        buf.Flush()
        pkts = writer.GetPacketsWritten()
        writer.Close()
        self.myinfo["packets_written"] = pkts
        if check_pkts:
            reader = target_io.EventFileReader(outfile)
            nevts = reader.GetNEvents()
            if nevts*self.kNPacketsPerEvent != pkts:
                logger.warning("number of events written " + str(nevts) + " does not match with packet written.")
                logger.warning("Packets written:" + str(pkts) + "Packets expected:" + str(nevts*self.kNPacketsPerEvent))
            self.myinfo["Nevents"] = nevts
            self.myinfo["packet_lost"] = nevts*self.kNPacketsPerEvent - pkts

        self.myinfo["temperatures"] = [self.temp1, self.temp2, self.temp3, self.temp4]
        logfile = os.path.splitext(outfile)[0]
        self.myinfo.save_logfile(logfile)
        del buf
        del writer
        del listener
        #gc.collect()

    def waitloop_datataking(self, time_to_wait):
        waited_time = 0
        time_step = 1
        manager = enlighten.get_manager()
        pbar = manager.counter(total=int(round(time_to_wait)), desc='Data acquisition', leave = False)
        while (waited_time < time_to_wait):
            pbar.update()
            thistime = time_step
            if waited_time + time_step > time_to_wait: thistime = time_to_wait - waited_time
            time.sleep(thistime) # wait some time to accumulate data
            waited_time += thistime
            #logger.log(logger.TEST_LEVEL_INFO, "-- Took data for {} of {} total seconds --".format(waited_time, time_to_wait))
            logger.info("-- Took data for {} of {} total seconds --".format(waited_time, time_to_wait))
        pbar.close()
        manager.stop()


    def triggerscan(self, group, trigger_duration, pmtref4_vec = None, thresh_vec = None, pbar=None, exttrig=False): # in s
        def efficiency(trig_eff_duration, exttrig=False): # in ns
            self.module.WriteSetting("TriggerEff_Duration", trig_eff_duration)
            if exttrig:
                reg_donebit = "TriggInputCounterDone"
                reg_counter = "TriggInputCounter"
            else:
                reg_donebit = "TriggerEff_DoneBit"
                reg_counter = "TriggEffCounter"
                
            #ret, done_bit = self.module.ReadSetting("TriggerEff_DoneBit")
            ret, done_bit = self.module.ReadSetting(reg_donebit)
            time.sleep(0.1)
            while done_bit == 0:
                #ret, done_bit = self.module.ReadSetting("TriggerEff_DoneBit")
                ret, done_bit = self.module.ReadSetting(reg_donebit)
            #ret, N = self.module.ReadSetting("TriggEffCounter")
            ret, N = self.module.ReadSetting(reg_counter)
            return N

        trig_eff_duration = int(trigger_duration / 8. * 1e9) # trigger_duration in s, trigger_eff  in ns
        if exttrig: 
            self.module.WriteSetting("ExtTriggerDirection", 0x0) ## set external trigger
            self.module.WriteSetting("TriggerEff_Enable", 2**group)
            ## setup the MUX
            if self.tbob:
              self.tbob.setmux(group)
            else:
                logger.error("No arduino on trigger board loaded. Could not set trigger group.")
                raise Exception("Error while setting trigger MUX")
        else:
            self.module.WriteSetting("TriggerEff_Enable", 2**group)
        pmtref4_name='PMTref4_'+str(int(group%4))
        thresh_name='Thresh_'+str(int(group%4))
        if pmtref4_vec is None and thresh_vec is None:
            logger.warning("no parameter to scan provided. Nothing done")
            out = None
        else:
            out = []
            if pmtref4_vec is not None and thresh_vec is None: #this is a scan over PMTRef4
                logger.log(logger.TEST_LEVEL_INFO, "Starting PMTRef4 scan over trigger group (0...15): " + str(group)) 
                for pmtref4 in pmtref4_vec: #range(pmtref4_start,pmtref4_stop,stepsize):
                    #self.module.WriteTriggerASICSetting(thresh_name, int(group/4), 2000, True)
                    self.module.WriteTriggerASICSetting(pmtref4_name, int(group/4), pmtref4, True)
                    time.sleep(0.1)
                    pbar.update()
                    counts=efficiency(trig_eff_duration, exttrig=exttrig)
                    rate=counts/trigger_duration  # Hz
                    out.append(rate)
                    logger.debug("Group " + str(group) + " pmtref4 " + str(pmtref4) + " rate " + str(rate) + " Hz")

            elif pmtref4_vec is None and thresh_vec is not None: #this is a scan over thresh
                logger.log(logger.TEST_LEVEL_INFO, "Starting Thresh scan over trigger group (0...15): " + str(group))

                for thresh in thresh_vec:
                    self.module.WriteTriggerASICSetting(thresh_name,int(group/4),thresh, True)
                    time.sleep(0.1)
                    pbar.update()
                    counts=efficiency(trig_eff_duration, exttrig=exttrig)
                    rate=counts/trigger_duration  # Hz
                    out.append(rate)
                    logger.debug ("Group " + str(group) + " thresh " + str(thresh) + " rate " + str(rate) + " Hz")


            else: #this is a 2D scan (veery slow, not tested!)
                for pmtref4 in pmtref4_vec:
                    out.append([])
                    self.module.WriteTriggerASICSetting(pmtref4_name,int(group/4),pmtref4, True)
                    time.sleep(0.1)
                    for thresh in thresh_vec:
                        self.module.WriteTriggerASICSetting(thresh_name,int(group/4),thresh, True)
                        time.sleep(0.1)
                        counts=efficiency(trig_eff_duration, exttrig=exttrig)
                        rate=counts/trigger_duration # Hz
                        out[-1].append(rate)
        return out
    
    def close(self):
        #self.module.DisableHVAll()
        self.module.CloseSockets()



def take_pedestal(outfile, nblocks=8, packets=8, daq_time=10., triggerdelay=500, vped=1200, sst=58, vtrim=1240, triggertype=1 ):
    logger.log(logger.TEST_LEVEL_INFO, "Start pedestal data taking...")
    moduleTC = TCModule(my_ip = "192.168.12.3", module_ip = "192.168.12.173", module_def=global_connection_details["module_def"],
                        asic_def=global_connection_details["asic_def"], trigger_asic_def=global_connection_details["trigger_asic_def"], reset=True, smart=True)
    logger.info("Number of blocks: " +str(nblocks))

    moduleTC.set_Vpeds(vped_file=None, vped=vped)
    moduleTC.set_SSToutFB_Vtrim(vtrim_file=None, vtrim=vtrim, sstoutfb=sst)
    
    moduleTC.prepare_daq(asics=None, nblocks = nblocks, triggerdelay=triggerdelay, packet_event=packets, triggertype=triggertype, triggermask=0x10000, warmup_time=60)

    if triggertype==1:
        moduleTC.reset_tbob_mux()
        #if moduleTC.tbob:
        #        logger.info("Setting trigger mux to ext/g0")
        #        moduleTC.tbob.setmux(0) #this is external trigger OR group0
        #else:
        #        logger.error("No arduino on trigger board loaded. Could not set trigger group.")
        #        raise Exception("Error while setting trigger MUX")


        moduleTC.daq(outfile, daq_time=daq_time, delay_loop=False, check_pkts=True)
    elif triggertype==2:
        moduleTC.daq(outfile, daq_time=0.05, delay_loop=True, check_pkts=True)

    moduleTC.close()
    logger.log(logger.TEST_LEVEL_INFO, "Finished pedestal data taking.")

    
def take_data(outfile, nblocks=8, packets=8, daq_time=10., triggerdelay=500, vped=1200, sst=58, vtrim=1240, triggertype=1, triggermask=0xffff, pmtref4=2000, thresh=2000):
    logger.log(logger.TEST_LEVEL_INFO,"Taking data")
    moduleTC = TCModule(my_ip = "192.168.12.3", module_ip = "192.168.12.173", module_def=global_connection_details["module_def"],
                        asic_def=global_connection_details["asic_def"], trigger_asic_def=global_connection_details["trigger_asic_def"], reset=True, smart=False)
    logger.info("Number of blocks:" + str(nblocks))

    moduleTC.set_Vpeds(vped_file=None, vped=vped)
    moduleTC.set_SSToutFB_Vtrim(vtrim_file=None, vtrim=vtrim, sstoutfb=sst)
    moduleTC.prepare_daq(asics=None, nblocks = nblocks, triggerdelay=triggerdelay, packet_event=packets, triggertype=triggertype, triggermask=triggermask, pmtref4=pmtref4, thresh=thresh, warmup_time=60)
    moduleTC.daq(outfile, daq_time=daq_time, delay_loop=False, check_pkts=True)
    moduleTC.close()


def take_data_sipm(outfile, nblocks=8, packets=8, daq_time=10., triggerdelay=500, vped=1200, sst=58, vtrim=1240, triggertype=1, triggermask=0xffff, pmtref4=1900, thresh=1800, enable_HV=False, disable_smart_channels=None, smart_dacs=100, smart_global=[0,0,63]):
    from SMART_utils import SMART
    
    logger.log(logger.TEST_LEVEL_INFO,"Taking SiPM data")
    moduleTC = TCModule(my_ip = "192.168.12.3", module_ip = "192.168.12.173", module_def=global_connection_details["module_def"],
                        asic_def=global_connection_details["asic_def"], trigger_asic_def=global_connection_details["trigger_asic_def"], reset=True, smart=True)
    logger.info("Number of blocks:" + str(nblocks))

    moduleTC.set_Vpeds(vped_file=None, vped=vped)
    moduleTC.set_SSToutFB_Vtrim(vtrim_file=None, vtrim=vtrim, sstoutfb=sst)
    moduleTC.prepare_daq(asics=None, nblocks = nblocks, triggerdelay=triggerdelay, packet_event=packets, triggertype=triggertype, triggermask=triggermask, pmtref4=pmtref4, thresh=thresh, warmup_time=10) ### change warmup time

    smart = SMART(moduleTC)
    smart.enable(asics=0xf)
    smart.reset(asics=0xf)
    smart.init_smart(dac_vals=smart_dacs, global_vals=smart_global, asics=0xf)
    smart.disable_channels64(channel_list=disable_smart_channels)

    moduleTC.myinfo["smart_dacs"] = smart_dacs
    moduleTC.myinfo["smart_globals"] = smart_global
    moduleTC.myinfo["smart_disable_channels"] = disable_smart_channels
    moduleTC.myinfo["hv_enable"] = enable_HV
    
    if enable_HV:
        moduleTC.module.WriteSetting("HV_enable",1)
        logger.debug("HV ON")
        curr,volts=moduleTC.read_hv()
        if volts<1.:
            logger.warning("HV was turned on, but measured value is too low: {0} V".format(volts))
        elif volts>150:
            logger.error("HV is too high! Measured value is: {0} V".format(volts))
            moduleTC.module.WriteSetting("HV_enable",0)
            raise Exception("HV turned off and exited.")
        time.sleep(0.5)

    moduleTC.daq(outfile, daq_time=daq_time, delay_loop=False, check_pkts=True)

    if enable_HV:
        moduleTC.module.WriteSetting("HV_enable",0)
        logger.debug("HV OFF")
        time.sleep(0.5)
        
    moduleTC.close()


def loop_take_data(outfile_list, cmd_list=None, nblocks=8, packets=8, daq_time=10., triggerdelay=500, vped=1200, sst=58, vtrim=1240, triggertype=1, triggermask=0xffff,pmtref4=2000, thresh=2000):
    ## take data multiple times without changing the setting. before each datataking a command is executed in the shell.
    ## If cmd_list is None, nothing is done between two data taking, so all data are taken in the same conditions.
    logger.log(logger.TEST_LEVEL_INFO,"Taking data")
    moduleTC = TCModule(my_ip = "192.168.12.3", module_ip = "192.168.12.173", module_def=global_connection_details["module_def"],
                        asic_def=global_connection_details["asic_def"], trigger_asic_def=global_connection_details["trigger_asic_def"], reset=True, smart=False)
    logger.info("Number of blocks: " + str(nblocks))

    moduleTC.set_Vpeds(vped_file=None, vped=vped)
    moduleTC.set_SSToutFB_Vtrim(vtrim_file=None, vtrim=vtrim, sstoutfb=sst)
    moduleTC.prepare_daq(asics=None, nblocks = nblocks, triggerdelay=triggerdelay, packet_event=packets, triggertype=triggertype, triggermask=triggermask,pmtref4=pmtref4, thresh=thresh, warmup_time=60)
    
    if cmd_list is None:
        cmd_list = [None]*len(outfile_list)
    for outfile, cmd in zip(outfile_list, cmd_list):
        if cmd is not None:
            logger.log(logger.TEST_LEVEL_INFO, "Amplitude: {0}V".format(cmd[0]))
            if os.path.exists(outfile):
               os.system("rm "+outfile)
            agilent33250A_inverted(cmd[0], cmd[1], 0)
            #logger.info(cmd)
            #os.system(cmd)
        else:
            logger.warning("No command provided in loop signal data taking. Nothing done before datataking.")
        moduleTC.daq(outfile, daq_time=daq_time, delay_loop=False, check_pkts=True)

    moduleTC.close()

def loop_take_data_sipm(outfile_list, smart_globals=None, nblocks=8, packets=8, daq_time=10., triggerdelay=500, vped=1200, sst=58, vtrim=1240, triggertype=1, triggermask=0xffff,pmtref4=2000, thresh=2000, enable_HV=False, disable_smart_channels=None, smart_dacs=100, smart_loop_globals=True, smart_loop_dacs=False):
    # smart globals must be a 2D list, each element made of 3 parameters. Ex: [ [0,0,63], [10,2,32], [18,6,12], ...]
    from SMART_utils import SMART

    if smart_loop_globals and smart_loop_dacs:
        msg = "Called SiPM loop function with both SMART DAC and globals flags. Please provide only one flag."
        logger.error(msg)
        raise Exception(msg)
    if not smart_loop_globals and not smart_loop_dacs:
        msg = "Called SiPM loop function without any loop flag. Please provide at least one flag."
        logger.error(msg)
        return
    
    if smart_globals is None:
        logger.error("Called SiPM loop function, but no SMART global parameters provided. Nothing done.")
        return
    elif type(smart_globals) is not list:
        logger.error("SMART global parameters provided in a wrong format. \
        Please provide a 1D or 2D list. Nothing done.")
        return
    elif smart_loop_globals:
            for smart_global in smart_globals:
                if len(smart_global)!=3:
                    logger.error("SMART global parameter provided in a wrong format. \
                    Each element must a list with 3 elements. Nothing done.")
                    return
    if smart_loop_dacs and type(smart_dacs) is not list:
        logger.error("SMART dac parameters provided in a wrong format. \
        Please provide a 1D or 2D list. Nothing done.")
        return
        

    logger.log(logger.TEST_LEVEL_INFO,"Taking SiPM data")
    moduleTC = TCModule(my_ip = "192.168.12.3", module_ip = "192.168.12.173", module_def=global_connection_details["module_def"],
                        asic_def=global_connection_details["asic_def"], trigger_asic_def=global_connection_details["trigger_asic_def"], reset=True, smart=True)
    logger.info("Number of blocks:" + str(nblocks))

    moduleTC.set_Vpeds(vped_file=None, vped=vped)
    moduleTC.set_SSToutFB_Vtrim(vtrim_file=None, vtrim=vtrim, sstoutfb=sst)
    moduleTC.prepare_daq(asics=None, nblocks = nblocks, triggerdelay=triggerdelay, packet_event=packets, triggertype=triggertype, triggermask=triggermask,pmtref4=pmtref4, thresh=thresh, warmup_time=10) ### change warmup time

    smart = SMART(moduleTC)
    smart.enable(asics=0xf)
    smart.reset(asics=0xf)
    moduleTC.myinfo["hv_enable"] = enable_HV
    
    if enable_HV:
        moduleTC.module.WriteSetting("HV_enable",1)
        logger.debug("HV ON")
        curr,volts=moduleTC.read_hv()
        if volts<1.:
            logger.warning("HV was turned on, but measured value is too low: {0} V".format(volts))
        elif volts>150:
            logger.error("HV is too high! Measured value is: {0} V".format(volts))
            moduleTC.module.WriteSetting("HV_enable",0)
            raise Exception("HV turned off and exited.")
        time.sleep(0.5)

    if smart_loop_globals:
        for outfile, smart_global in zip(outfile_list,smart_globals):
            moduleTC.myinfo["smart_dacs"] = smart_dacs
            moduleTC.myinfo["smart_globals"] = smart_global
            moduleTC.myinfo["smart_disable_channels"] = disable_smart_channels
            logger.log(logger.TEST_LEVEL_INFO, "SMART globals: {0} {1} {2}".format(smart_global[0],smart_global[1],smart_global[2]))
            if os.path.exists(outfile):
                os.system("rm "+outfile)
            smart.init_smart(dac_vals=smart_dacs, global_vals=smart_global, asics=0xf)
            smart.disable_channels64(channel_list=disable_smart_channels)
            moduleTC.daq(outfile, daq_time=daq_time, delay_loop=False, check_pkts=True)
            time.sleep(0.5)
            
    if smart_loop_dacs:
        for outfile, smart_dac in zip(outfile_list,smart_dacs):
            moduleTC.myinfo["smart_dacs"] = smart_dac
            moduleTC.myinfo["smart_globals"] = smart_globals
            moduleTC.myinfo["smart_disable_channels"] = disable_smart_channels
            if type(smart_dac) is list:
                dac_string = " ".join([str(d) for d in smart_dac])
            else:
                dac_string = str(smart_dac)
            logger.log(logger.TEST_LEVEL_INFO, "SMART DAC: {0} ".format(dac_string))
            if os.path.exists(outfile):
                os.system("rm "+outfile)
            smart.init_smart(dac_vals=smart_dac, global_vals=smart_globals, asics=0xf)
            smart.disable_channels64(channel_list=disable_smart_channels)
            moduleTC.daq(outfile, daq_time=daq_time, delay_loop=False, check_pkts=True)
            time.sleep(0.5)
           
        
    if enable_HV:
        moduleTC.module.WriteSetting("HV_enable",0)
        logger.debug("HV OFF")
        time.sleep(0.5)

    moduleTC.close()

def do_triggerscan(outfilename, groups=range(16), trigger_duration = 0.1, pmtref4_vec=None, thresh_vec=None, vped=1200, wbias=985, pmtref4=2000, thresh=2000,gain=0x15, exttrig=False):
    moduleTC = TCModule(my_ip = "192.168.12.3", module_ip = "192.168.12.173", module_def=global_connection_details["module_def"],
                        asic_def=global_connection_details["asic_def"], trigger_asic_def=global_connection_details["trigger_asic_def"], reset=True, smart=False)
    moduleTC.set_Vpeds(vped_file=None, vped=vped)
    moduleTC.module.WriteSetting("TACK_EnableTrigger", 0) #disable data trigger
    logger.info("do_triggerscan: pmtref4 --> " +str(pmtref4))
    moduleTC.set_trigger_params(wbias=wbias, pmtref4=pmtref4, thresh=thresh, gain=gain)
    outfiles = []
    logger.info("PMTref4_vec = " + str(pmtref4_vec))
    logger.info("thresh_vec = " + str(thresh_vec))


    manager = enlighten.get_manager()
    if pmtref4_vec is not None and thresh_vec is None: #this is a scan over PMTRef4
        pbar = manager.counter(total=len(pmtref4_vec)*len(groups), desc='PMTref4 scan', leave = False)
    if pmtref4_vec is None and thresh_vec is not None: #this is a scan over thresh
        pbar = manager.counter(total=len(thresh_vec)*len(groups), desc='thresh scan', leave = False)

    for group in groups:
        outfile = outfilename+"_group"+str(group)+".yaml"
        rates = moduleTC.triggerscan(group, trigger_duration, pmtref4_vec = pmtref4_vec, thresh_vec = thresh_vec, pbar=pbar, exttrig=exttrig) # in s
        d = {}
        try:
            pmtref4_vec = pmtref4_vec.tolist()
        except:
            pass
        try:
            thresh_vec = thresh_vec.tolist()
        except:
            pass
        d["pmtref4"] = pmtref4_vec
        d["thresh"] = thresh_vec
        d["trigger_duration"] = trigger_duration
        d["rates"] = rates
        with open(outfile,"w") as fptr:
            fptr.write(yaml.dump(d, default_flow_style=False))
        outfiles.append(outfile)
  
    #reset the trigger mux to group0 (which is in OR with external trigger)
    moduleTC.reset_tbob_mux()
    #if moduleTC.tbob:
    #            moduleTC.tbob.setmux(0)
    #else:
    #            logger.error("No arduino on trigger board loaded. Could not set trigger group.")
    #            raise Exception("Error while setting trigger MUX")



    pbar.close()
    manager.stop()

    moduleTC.close()
    return outfiles


def do_triggerscan_sipm(outfilename, groups=range(16), trigger_duration = 0.1, pmtref4_vec=None, thresh_vec=None, vped=1200, wbias=985, pmtref4=2000, thresh=2000,gain=0x15, exttrig=False, enable_HV=True, disable_smart_channels=None, smart_dacs=100, smart_global=[0,0,63]):
    from SMART_utils import SMART
    moduleTC = TCModule(my_ip = "192.168.12.3", module_ip = "192.168.12.173", module_def=global_connection_details["module_def"],
                        asic_def=global_connection_details["asic_def"], trigger_asic_def=global_connection_details["trigger_asic_def"], reset=True, smart=True)

    moduleTC.set_Vpeds(vped_file=None, vped=vped)
    moduleTC.module.WriteSetting("TACK_EnableTrigger", 0) #disable data trigger
    logger.info("do_triggerscan_sipm: pmtref4 --> " +str(pmtref4))
    moduleTC.set_trigger_params(wbias=wbias, pmtref4=pmtref4, thresh=thresh, gain=gain)
    outfiles = []
    logger.info("PMTref4_vec = " + str(pmtref4_vec))
    logger.info("thresh_vec = " + str(thresh_vec))

    smart = SMART(moduleTC)
    smart.enable(asics=0xf)
    smart.reset(asics=0xf)
    smart.init_smart(dac_vals=smart_dacs, global_vals=smart_global, asics=0xf)
    smart.disable_channels64(channel_list=disable_smart_channels)
    if enable_HV:
        moduleTC.module.WriteSetting("HV_enable",1)
        logger.debug("HV ON")
        curr,volts=moduleTC.read_hv()
        if volts<1.:
            logger.warning("HV was turned on, but measured value is too low: {0} V".format(volts))
        elif volts>150:
            logger.error("HV is too high! Measured value is: {0} V".format(volts))
            moduleTC.module.WriteSetting("HV_enable",0)
            raise Exception("HV turned off and exited.")

    manager = enlighten.get_manager()
    if pmtref4_vec is not None and thresh_vec is None: #this is a scan over PMTRef4
        pbar = manager.counter(total=len(pmtref4_vec)*len(groups), desc='PMTref4 scan', leave = False)
    if pmtref4_vec is None and thresh_vec is not None: #this is a scan over thresh
        pbar = manager.counter(total=len(thresh_vec)*len(groups), desc='thresh scan', leave = False)

    for group in groups:
        outfile = outfilename+"_group"+str(group)+".yaml"
        rates = moduleTC.triggerscan(group, trigger_duration, pmtref4_vec = pmtref4_vec, thresh_vec = thresh_vec, pbar=pbar, exttrig=exttrig) # in s
        d = {}
        try:
            pmtref4_vec = pmtref4_vec.tolist()
        except:
            pass
        try:
            thresh_vec = thresh_vec.tolist()
        except:
            pass
        d["pmtref4"] = pmtref4_vec
        d["thresh"] = thresh_vec
        d["trigger_duration"] = trigger_duration
        d["rates"] = rates
        with open(outfile,"w") as fptr:
            fptr.write(yaml.dump(d, default_flow_style=False))
        outfiles.append(outfile)
  
    #reset the trigger mux to group0 (which is in OR with external trigger)
    moduleTC.reset_tbob_mux()
    #if moduleTC.tbob:
    #            moduleTC.tbob.setmux(0)
    #else:
    #            logger.error("No arduino on trigger board loaded. Could not set trigger group.")
    #            raise Exception("Error while setting trigger MUX")



    pbar.close()
    manager.stop()
    
    if enable_HV:
        moduleTC.module.WriteSetting("HV_enable",0)
        logger.debug("HV OFF")
    
    moduleTC.close()
    return outfiles



def do_calib_smart(smart_dacs=100,smart_global=[0,0,63], outfilename=None):
    from SMART_utils import SMART

    logger.log(logger.TEST_LEVEL_INFO,"Calibrating SMART")
    moduleTC = TCModule(my_ip = "192.168.12.3", module_ip = "192.168.12.173", module_def=global_connection_details["module_def"],
                        asic_def=global_connection_details["asic_def"], trigger_asic_def=global_connection_details["trigger_asic_def"], reset=True, smart=True)

    smart = SMART(moduleTC)
    smart.enable(asics=0xf)
    smart.reset(asics=0xf)
    #smart.config_global(r=smart_global[0],c=smart_global[1],pz=smart_global[2], asics=0xf)
    smart.init_smart(dac_vals=smart_dacs, global_vals=smart_global, asics=0xf)

    ## Be sure HV is off
    moduleTC.module.WriteSetting("HV_enable",0)
    logger.debug("HV OFF")
        
    calib_vals, allADCval_mean, allADCval_sigma = smart.calib_adc(asics=0xf, full_output=True)
    if outfilename is not None:
        np.savetxt(outfilename+"_calib.txt", calib_vals, fmt="%3d")
        np.savetxt(outfilename+"_adc_mean.txt", allADCval_mean, fmt="%.2f")
        np.savetxt(outfilename+"_adc_sigma.txt", allADCval_sigma, fmt="%.2f")

    moduleTC.close()

    return calib_vals, allADCval_mean, allADCval_sigma

def do_power(outdir): #test_voltages
    moduleTC = TCModule(my_ip = "192.168.12.3", module_ip = "192.168.12.173", module_def=global_connection_details["module_def"],
                        asic_def=global_connection_details["asic_def"], trigger_asic_def=global_connection_details["trigger_asic_def"], reset=True, smart=False)

    d = {}
    TEMP_PRIMARY, TEMP_AUX, _, _ = moduleTC.read_temperatures()

    d["TEMP_PRIMARY"] = TEMP_PRIMARY
    d["TEMP_AUX"] = TEMP_AUX



    moduleTC.module.WriteSetting("HV_enable",1)
    logger.debug("HV ON")
    #ret, voltage = module.ReadHVVoltageInput()
    #ret, current = module.ReadHVCurrentInput()

    time.sleep(10)


    #power supply: 31.4 V
    #tbob 2, measured on R70: 30.7 V (some voltage drop along channels)
    #measured raw value (HV): 432 adc unit
    #calibration value: 30.7V / 432 = 0.711
    #maybe should calbirate the other channels too...

    if moduleTC.sbob1:
        voltage_sbob1_hv1_hvon, voltage_sbob1_hv1_hvon_raw = moduleTC.sbob1.read_hv(1)
        voltage_sbob1_hv2_hvon, voltage_sbob1_hv2_hvon_raw = moduleTC.sbob1.read_hv(2)
    else:
        voltage_sbob1_hv1_hvon, voltage_sbob1_hv1_hvon_raw = -1., -1.
        voltage_sbob1_hv2_hvon, voltage_sbob1_hv2_hvon_raw = -1., -1.
    if moduleTC.sbob2:
        voltage_sbob2_hv1_hvon, voltage_sbob2_hv1_hvon_raw = moduleTC.sbob2.read_hv(1)
        voltage_sbob2_hv2_hvon, voltage_sbob2_hv2_hvon_raw = moduleTC.sbob2.read_hv(2)
    else:
        voltage_sbob2_hv1_hvon, voltage_sbob2_hv1_hvon_raw = -1., -1.
        voltage_sbob2_hv2_hvon, voltage_sbob2_hv2_hvon_raw = -1., -1.




    HV_CURRENT_ON_AMPERES, HV_VOLTAGE_ON_VOLTS = moduleTC.read_hv()
    logger.debug("voltage_sbob1_hv1_hvon = " + ('{:.2f}'.format(voltage_sbob1_hv1_hvon)) + " V (raw " + str(voltage_sbob1_hv1_hvon_raw) + ")")
    logger.debug("voltage_sbob1_hv2_hvon = " + ('{:.2f}'.format(voltage_sbob1_hv2_hvon)) + " V (raw " + str(voltage_sbob1_hv2_hvon_raw) + ")")
    logger.debug("voltage_sbob2_hv1_hvon = " + ('{:.2f}'.format(voltage_sbob2_hv1_hvon)) + " V (raw " + str(voltage_sbob2_hv1_hvon_raw) + ")")
    logger.debug("voltage_sbob2_hv2_hvon = " + ('{:.2f}'.format(voltage_sbob2_hv2_hvon)) + " V (raw " + str(voltage_sbob2_hv2_hvon_raw) + ")")


    moduleTC.module.WriteSetting("HV_enable", 0)
    logger.debug("HV OFF")
    time.sleep(1)



    if moduleTC.sbob1:
        voltage_sbob1_hv1_hvoff, voltage_sbob1_hv1_hvoff_raw = moduleTC.sbob1.read_hv(1)
        voltage_sbob1_hv2_hvoff, voltage_sbob1_hv2_hvoff_raw = moduleTC.sbob1.read_hv(2)
    else:
        voltage_sbob1_hv1_hvoff, voltage_sbob1_hv1_hvoff_raw = -1., -1.
        voltage_sbob1_hv2_hvoff, voltage_sbob1_hv2_hvoff_raw = -1., -1.
    if moduleTC.sbob2:        
        voltage_sbob2_hv1_hvoff, voltage_sbob2_hv1_hvoff_raw = moduleTC.sbob2.read_hv(1)
        voltage_sbob2_hv2_hvoff, voltage_sbob2_hv2_hvoff_raw = moduleTC.sbob2.read_hv(2)
    else:
        voltage_sbob2_hv1_hvoff, voltage_sbob2_hv1_hvoff_raw = -1., -1.
        voltage_sbob2_hv2_hvoff, voltage_sbob2_hv2_hvoff_raw = -1., -1.
        
    HV_CURRENT_OFF_AMPERES, HV_VOLTAGE_OFF_VOLTS = moduleTC.read_hv()
    logger.debug("voltage_sbob1_hv1_hvoff = " + ('{:.2f}'.format(voltage_sbob1_hv1_hvoff)) + " V (raw " + str(voltage_sbob1_hv1_hvoff_raw) +")")
    logger.debug("voltage_sbob1_hv2_hvoff = " + ('{:.2f}'.format(voltage_sbob1_hv2_hvoff)) + " V (raw " + str(voltage_sbob1_hv2_hvoff_raw) +")")
    logger.debug("voltage_sbob2_hv1_hvoff = " + ('{:.2f}'.format(voltage_sbob2_hv1_hvoff)) + " V (raw " + str(voltage_sbob2_hv1_hvoff_raw) +")")
    logger.debug("voltage_sbob2_hv2_hvoff = " + ('{:.2f}'.format(voltage_sbob2_hv2_hvoff)) + " V (raw " + str(voltage_sbob2_hv2_hvoff_raw) +")")

    if moduleTC.sbob1:
        voltage_sbob1_3v3a, voltage_sbob1_3v3a_raw = moduleTC.sbob1.read_voltage("3V3A")
        voltage_sbob1_3v3b, voltage_sbob1_3v3b_raw = moduleTC.sbob1.read_voltage("3V3B")
        voltage_sbob1_5v0a, voltage_sbob1_5v0a_raw = moduleTC.sbob1.read_voltage("5V0A")
        voltage_sbob1_5v0b, voltage_sbob1_5v0b_raw = moduleTC.sbob1.read_voltage("5V0B")
    else:
        voltage_sbob1_3v3a, voltage_sbob1_3v3a_raw = -1., -1.
        voltage_sbob1_3v3b, voltage_sbob1_3v3b_raw = -1., -1.
        voltage_sbob1_5v0a, voltage_sbob1_5v0a_raw = -1., -1.
        voltage_sbob1_5v0b, voltage_sbob1_5v0b_raw = -1., -1.
        
    if moduleTC.sbob2:        
        voltage_sbob2_3v3a, voltage_sbob2_3v3a_raw = moduleTC.sbob2.read_voltage("3V3A")
        voltage_sbob2_3v3b, voltage_sbob2_3v3b_raw = moduleTC.sbob2.read_voltage("3V3B")
        voltage_sbob2_5v0a, voltage_sbob2_5v0a_raw = moduleTC.sbob2.read_voltage("5V0A")
        voltage_sbob2_5v0b, voltage_sbob2_5v0b_raw = moduleTC.sbob2.read_voltage("5V0B")
    else:
        voltage_sbob2_3v3a, voltage_sbob2_3v3a_raw = -1., -1.
        voltage_sbob2_3v3b, voltage_sbob2_3v3b_raw = -1., -1.
        voltage_sbob2_5v0a, voltage_sbob2_5v0a_raw = -1., -1.
        voltage_sbob2_5v0b, voltage_sbob2_5v0b_raw = -1., -1.
 
    logger.debug("voltage_3v3_1a = " + ('{:.2f}'.format(voltage_sbob1_3v3a)) + " V (raw " + str(voltage_sbob1_3v3a_raw) + ")")
    logger.debug("voltage_3v3_1b = " + ('{:.2f}'.format(voltage_sbob1_3v3b)) + " V (raw " + str(voltage_sbob1_3v3b_raw) + ")")
    logger.debug("voltage_3v3_2a = " + ('{:.2f}'.format(voltage_sbob2_3v3a)) + " V (raw " + str(voltage_sbob2_3v3a_raw) + ")")
    logger.debug("voltage_3v3_2b = " + ('{:.2f}'.format(voltage_sbob2_3v3b)) + " V (raw " + str(voltage_sbob2_3v3b_raw) + ")")
    logger.debug("voltage_5v0_1a = " + ('{:.2f}'.format(voltage_sbob1_5v0a)) + " V (raw " + str(voltage_sbob1_5v0a_raw) + ")")
    logger.debug("voltage_5v0_1b = " + ('{:.2f}'.format(voltage_sbob1_5v0b)) + " V (raw " + str(voltage_sbob1_5v0b_raw) + ")")
    logger.debug("voltage_5v0_2a = " + ('{:.2f}'.format(voltage_sbob2_5v0a)) + " V (raw " + str(voltage_sbob2_5v0a_raw) + ")")
    logger.debug("voltage_5v0_2b = " + ('{:.2f}'.format(voltage_sbob2_5v0b)) + " V (raw " + str(voltage_sbob2_5v0b_raw) + ")")

    d["HV_CURRENT_OFF_AMPERES"] = HV_CURRENT_OFF_AMPERES
    d["HV_VOLTAGE_OFF_VOLTS"] = HV_VOLTAGE_OFF_VOLTS
    d["HV_CURRENT_ON_AMPERES"] = HV_CURRENT_ON_AMPERES
    d["HV_VOLTAGE_ON_VOLTS"] = HV_VOLTAGE_ON_VOLTS
    d["PRIMARY_HV1_HVON_VOLTS"] = voltage_sbob1_hv1_hvon
    d["PRIMARY_HV2_HVON_VOLTS"] = voltage_sbob1_hv2_hvon
    d["AUX_HV1_HVON_VOLTS"] = voltage_sbob2_hv1_hvon
    d["AUX_HV2_HVON_VOLTS"] = voltage_sbob2_hv2_hvon
    d["PRIMARY_HV1_HVOFF_VOLTS"] = voltage_sbob1_hv1_hvoff
    d["PRIMARY_HV2_HVOFF_VOLTS"] = voltage_sbob1_hv2_hvoff
    d["AUX_HV1_HVOFF_VOLTS"] = voltage_sbob2_hv1_hvoff
    d["AUX_HV2_HVOFF_VOLTS"] = voltage_sbob2_hv2_hvoff
    d["PRIMARY_3V3A_VOLTS"] = voltage_sbob1_3v3a
    d["PRIMARY_3V3B_VOLTS"] = voltage_sbob1_3v3b
    d["AUX_3V3A_VOLTS"] = voltage_sbob2_3v3a
    d["AUX_3V3B_VOLTS"] = voltage_sbob2_3v3b
    d["PRIMARY_5V0A_VOLTS"] = voltage_sbob1_5v0a
    d["PRIMARY_5V0B_VOLTS"] = voltage_sbob1_5v0b
    d["AUX_5V0A_VOLTS"] = voltage_sbob2_5v0a
    d["AUX_5V0B_VOLTS"] = voltage_sbob2_5v0b

    d["PRIMARY_HV1_HVON_RAW"] = voltage_sbob1_hv1_hvon_raw
    d["PRIMARY_HV2_HVON_RAW"] = voltage_sbob1_hv2_hvon_raw
    d["AUX_HV1_HVON_RAW"] = voltage_sbob2_hv1_hvon_raw
    d["AUX_HV2_HVON_RAW"] = voltage_sbob2_hv2_hvon_raw
    d["PRIMARY_HV1_HVOFF_RAW"] = voltage_sbob1_hv1_hvoff_raw
    d["PRIMARY_HV2_HVOFF_RAW"] = voltage_sbob1_hv2_hvoff_raw
    d["AUX_HV1_HVOFF_RAW"] = voltage_sbob2_hv1_hvoff_raw
    d["AUX_HV2_HVOFF_RAW"] = voltage_sbob2_hv2_hvoff_raw
    d["PRIMARY_3V3A_RAW"] = voltage_sbob1_3v3a_raw
    d["PRIMARY_3V3B_RAW"] = voltage_sbob1_3v3b_raw
    d["AUX_3V3A_RAW"] = voltage_sbob2_3v3a_raw
    d["AUX_3V3B_RAW"] = voltage_sbob2_3v3b_raw
    d["PRIMARY_5V0A_RAW"] = voltage_sbob1_5v0a_raw
    d["PRIMARY_5V0B_RAW"] = voltage_sbob1_5v0b_raw
    d["AUX_5V0A_RAW"] = voltage_sbob2_5v0a_raw
    d["AUX_5V0B_RAW"] = voltage_sbob2_5v0b_raw

    d["PRIMARY_HV_CALIB_MULT_HV1"] = ArduinoSBOB.HV_CALIB_MULT_SBOB1_HV1
    d["PRIMARY_HV_CALIB_MULT_HV2"] = ArduinoSBOB.HV_CALIB_MULT_SBOB1_HV2
    d["AUX_HV_CALIB_MULT_HV1"] = ArduinoSBOB.HV_CALIB_MULT_SBOB2_HV1
    d["AUX_HV_CALIB_MULT_HV2"] = ArduinoSBOB.HV_CALIB_MULT_SBOB2_HV2
    d["PRIMARY_CALIB_MULT_3V3A"] = ArduinoSBOB.HV_CALIB_MULT_SBOB1_3V3A
    d["PRIMARY_CALIB_MULT_3V3B"] = ArduinoSBOB.HV_CALIB_MULT_SBOB1_3V3B
    d["AUX_HV_CALIB_MULT_3V3A"] = ArduinoSBOB.HV_CALIB_MULT_SBOB2_3V3A
    d["AUX_HV_CALIB_MULT_3V3B"] = ArduinoSBOB.HV_CALIB_MULT_SBOB2_3V3B
    d["PRIMARY_HV_CALIB_MULT_5V0A"] = ArduinoSBOB.HV_CALIB_MULT_SBOB1_5V0A
    d["PRIMARY_HV_CALIB_MULT_5V0B"] = ArduinoSBOB.HV_CALIB_MULT_SBOB1_5V0B
    d["AUX_HV_CALIB_MULT_5V0A"] = ArduinoSBOB.HV_CALIB_MULT_SBOB2_5V0A
    d["AUX_HV_CALIB_MULT_5V0B"] = ArduinoSBOB.HV_CALIB_MULT_SBOB2_5V0B


    #FEETestEnable_Primary 0x35	12	0	  0x0		0	0x0	0xFFF 	0.	0.	 Select which channels should be enabled, mask, Bits assigned as followed: 0 - smart_datain0, 1 - smart_datain1 , 2 - smart_spi_clk, 3 - smart_spi_res, 4 - mosi_music, 5 - miso_music, 6 - sclk_music, 7 - reset_music, 8 - ss_music0, 9 - ss_music1, 10 - ss_music2, 11 - ss_music3
    #FEETestSelect_Primary 0x35	12	12	0x0		0	0x0	0xFFF 	0.	0.	 Select if clock or High assigned, mask as above
    #FEE_Clock_Primary     0x35	5  	24	0xF		0	0x0	0x1F 	0.	0.	 FFE Test clock divider. Clock period is 8ns*2**value, i.e. 17 => 953Hz
    #FEETest_Start_Primary 0x35  1   29	0x0		1	0x0	0x0 	0.	0.	 Not used at the moment, will be implemented when real SPI also in use
    #FEE_Response_Primary  0x35	2   30	0x0		1	0x0	0x2 	0.	0.	 Reading from input pins, bit 0 - smart_dataout0, 1 - smart_dataout1
    #FEETestEnable_Aux 0x36	12	0	  0x0		0	0x0	0xFFF 	0.	0.	 
    #Select which channels should be enabled, mask, Bits assigned as followed: 0 - smart_datain0, 1 - smart_datain1 , 2 - smart_spi_clk, 3 - smart_spi_res, 4 - mosi_music, 5 - miso_music, 6 - sclk_music, 7 - reset_music, 8 - ss_music0, 9 - ss_music1, 10 - ss_music2, 11 - ss_music3
    #FEETestSelect_Aux 0x36	12	12	0x0		0	0x0	0xFFF 	0.	0.	 Select if clock or High assigned, mask as above
    #FEE_Clock_Aux     0x36	5  	24	0xF		0	0x0	0x1F 	0.	0.	 FFE Test clock divider. Clock period is 8ns*2**value, i.e. 17 => 953Hz
    #FEETest_Start_Aux 0x36  1   29	0x0		1	0x0	0x0 	0.	0.	 Not used at the moment, will be implemented when real SPI also in use
    #FEE_Response_Aux  0x36	2   30	0x0		1	0x0	0x2 	0.	0.	 Reading from input pins, bit 0 - smart_dataout0, 1 - smart_dataout1


    #divider 0: --> 62500000 Hz, 8 ns halfperiod
    #divider 1: --> 31250000 Hz, 16 ns halfperiod
    #divider 2: --> 15625000 Hz, 32 ns halfperiod
    #divider 3: --> 7812500 Hz, 64 ns halfperiod
    #divider 4: --> 3906250 Hz, 128 ns halfperiod
    #divider 5: --> 1953125 Hz, 256 ns halfperiod
    #divider 6: --> 976562 Hz, 512 ns halfperiod
    #divider 7: --> 488281 Hz, 1024 ns halfperiod
    #divider 8: --> 244141 Hz, 2048 ns halfperiod
    #divider 9: --> 122070 Hz, 4096 ns halfperiod
    #divider 10: --> 61035 Hz, 8192 ns halfperiod
    #divider 11: --> 30518 Hz, 16384 ns halfperiod
    #divider 12: --> 15259 Hz, 32768 ns halfperiod
    #divider 13: --> 7629 Hz, 65536 ns halfperiod
    #divider 14: --> 3815 Hz, 131072 halfperiod
    #divider 15: --> 1907 Hz, 262144 ns halfperiod
    #divider 16: --> 954 Hz, 524288 ns halfperiod
    #divider 17: --> 477 Hz, 1048576 ns halfperiod
    #divider 18: --> 238 Hz, 2097152 ns halfperiod
    #divider 19: --> 119 Hz, 4194304 ns halfperiod
    #divider above 19 not working! (wrong)
    
    bit_name = [None]*12
    bit_name[0] = "SMART_DATAIN0"
    bit_name[1] = "SMART_DATAIN1"
    bit_name[2] = "SMART_SPI_CLK"
    bit_name[3] = "SMART_SPI_RES"
    bit_name[4] = "MOSI_MUSIC"
    bit_name[5] = "MISO_MUSIC"
    bit_name[6] = "SCLK_MUSIC"
    bit_name[7] = "RESET_MUSIC"
    bit_name[8] = "SS_MUSIC0"
    bit_name[9] = "SS_MUSIC1"
    bit_name[10] = "SS_MUSIC2"
    bit_name[11] = "SS_MUSIC3"
    loopback_pin_name = ["SMART_DATAOUT0", "SMART_DATAOUT1"]


    #half period 
    a=2751.07/2.0 #divided by two since we are actually measuring the half period (2751.07 is giving the full period length)
    b=1.31
    d["CLOCK_CALIBRATION_ADD"]=b
    d["CLOCK_CALIBRATION_MULT"]=a


    logger.debug("Clock divider table:")
    
    for clock_divider in range(0, 20):
        logger.debug("divider {}: --> frequency  {:.0f} Hz".format(clock_divider, 1/(2*(8.0e-9)*float(1 << clock_divider))))
    for clock_divider in range(0, 20):
        logger.debug("divider {}: --> halfperiod {:.0f} ns".format(clock_divider, (8.0)*float(1 << clock_divider)))
    for clock_divider in range(0, 20):
        logger.debug("divider {}: --> halfperiod {:.0f} us".format(clock_divider, (8.0)*float(1 << clock_divider)/1000.0))
   
    manager = enlighten.get_manager()
    #pbar = manager.counter(total=20 + 20*2 + 4 + 4, desc='Voltage levels and clock injection test', leave = False)
    pbar = manager.counter(total=20 + 20*2 + 4, desc='Voltage levels and clock injection test', leave = False)


    for bob in [1,2]:
        type = None
        name = None
        if bob == 1:
            type = "Primary"
            name = "PRIMARY"
        else:
            type = "Aux"
            name = "AUX"
        bobinstance = None
        if bob == 1:
            bobinstance = moduleTC.sbob1
        else:
            bobinstance = moduleTC.sbob2
        

        for i in [0,1]: #the two loopback pins (smart data out) 
          moduleTC.module.WriteSetting("FEETestEnable_" + type, 0)
          moduleTC.module.WriteSetting("FEETestSelect_" + type, 0) #1 --> clock 0 --> high
          time.sleep(0.1)
          ret, test = moduleTC.module.ReadSetting("FEE_Response_" + type)
          result = (test >> i) & 1
          logger.debug(name + " " + loopback_pin_name[i] + ": Expected 0, read: " + str(result))
          d[name + "_" + loopback_pin_name[i] + "_ZERO_BEFORE"] =  result
          moduleTC.module.WriteSetting("FEETestEnable_" + type, 1 << i)
          time.sleep(0.1)
          ret, test = moduleTC.module.ReadSetting("FEE_Response_" + type)
          result = (test >> i) & 1
          logger.debug(name + " " + loopback_pin_name[i] + ": Expected 1, read: " + str(result))
          d[name + "_" + loopback_pin_name[i] + "_ONE"] =  result
          moduleTC.module.WriteSetting("FEETestEnable_" + type, 0x00)
          time.sleep(0.1)
          ret, test = moduleTC.module.ReadSetting("FEE_Response_" + type)
          result = (test >> i) & 1
          logger.debug(name + " " + loopback_pin_name[i] + ": Expected 0, read: " + str(result))
          d[name + "_" + loopback_pin_name[i] + "_ZERO_AFTER"] =  result   
          pbar.update()

        for i in range(2,12):
          moduleTC.module.WriteSetting("FEETestEnable_" + type, 0x00)
          moduleTC.module.WriteSetting("FEETestSelect_" + type, 0x00) #1 --> clock 0 --> high
          time.sleep(0.1)
          res = bobinstance.read_logic(bit_name[i])
          logger.debug(name + " " + bit_name[i] + ": Expected 0, read: " + str(res))
          d[name + "_" + bit_name[i] + "_ZERO_BEFORE"] = res

          moduleTC.module.WriteSetting("FEETestEnable_" + type, 1 << i)
          moduleTC.module.WriteSetting("FEETestSelect_" + type, 0x00) #1 --> clock 0 --> high
          time.sleep(0.1)
          res = bobinstance.read_logic(bit_name[i])
          logger.debug(name + " " + bit_name[i] + ": Expected 1, read: " + str(res))
          d[name + "_" + bit_name[i] + "_ONE"] = res
          moduleTC.module.WriteSetting("FEETestEnable_" + type, 0x00)
          moduleTC.module.WriteSetting("FEETestSelect_" + type, 0x00) #1 --> clock 0 --> high
          time.sleep(0.1)
          res = bobinstance.read_logic(bit_name[i])
          logger.debug(name + " " + bit_name[i] + ": Expected 0, read: " + str(res))
          d[name + "_" + bit_name[i] + "_ZERO_AFTER"] = res
          pbar.update()
       #clock divider 10 is about 120 kHz
       #clock divider 16 is about 954 Hz
       #divider above 19 doesn't work, 20 is the same as 16 (954 Hz), 21==17, 22==18, 23==19, 24==16, 25==17, 26==18, 27==19, 28==16, 29==17, 30==18, 31==19
       #note: if I set the arduino timeout (maxloops) to 30000UL, with clock_divider = 16 I get about 75 samples, so the timeout 30000UL is actually about 78 ms...

        '''
        AR: this part was removed because the software polling method for measuring clock speed is not reliable so it's commented out, can be removed

        for clock_divider in [16]: #software polling on DATAOUT* clocks only with slow clock (DIVIDER=16)


          for i in [0,1]: #this is the index of "smartdataout" (loopback pin): 0, 1
            res = moduleTC.module.WriteSetting("FEETestEnable_" + type, 1 << i) #1 --> clock 0 --> high
            #logger.debug("test enable " + type + " result: " + str(res))
            res = moduleTC.module.WriteSetting("FEETestSelect_" + type, 1 << i) #1 --> clock 0 --> high
            #logger.debug("test select " + type + " result: " + str(res))
            res = moduleTC.module.WriteSetting("FEE_Clock_" + type, clock_divider) #maximum is 0x1f or 31
            expected_halfperiod_microseconds = (8.0/1000.0)*float(1 << clock_divider)
            expected_frequency_hz = 1.0/(2.0*expected_halfperiod_microseconds*1.0e6)
            logger.debug("{}: SW_POLLING: setting clock speed of pin {} to {:.1f} Hz, expected halfperiod (us): {:.1f} ".format(type, loopback_pin_name[i], expected_frequency_hz, expected_halfperiod_microseconds ))
            
            NSAMPLES =  1000 #software polling (NSAMPLES times)
            values = [0] * NSAMPLES
            errorlevel = [0] * NSAMPLES
            timestamps = [datetime.datetime(1970,1,1)] * NSAMPLES
            for j in range(0, NSAMPLES):
              errorlevel[j], test = moduleTC.module.ReadSetting("FEE_Response_" + type)
              values[j] = (test >> i) & 1
              timestamps[j] = datetime.datetime.now()



            first_rising_edge_index = -1
            for j in range(1, NSAMPLES):
              if values[j] == 1 and values[j-1] == 0:
                first_rising_edge_index = j
                break
            
            nsamples = 0
            avg = 0
            stddev = 0
            agv = 0
            min_hp = 0
            max_hp = 0
            if (first_rising_edge_index == -1):
               logger.error("No transition found while checking " + name + loopback_pin_name[i])
            
            else :
              previous_value = values[first_rising_edge_index]
              previous_switch_time = timestamps[first_rising_edge_index]
              transitions = []


              count = 0
              for j in range(first_rising_edge_index, NSAMPLES):  
                 #diff = timestamps[j] - timestamps[0]  
                 if previous_value != values[j]: 
                   halfperiod = timestamps[j] - previous_switch_time
                   transitions.append(halfperiod)
                   previous_switch_time = timestamps[j]
                   logger.debug("halfperiod " + str(count) + ": " + str(halfperiod.microseconds+(1000000*halfperiod.seconds)) + " us")
                   count += 1
                 previous_value = values[j]

              sumhalfperiods = 0
              n = 0
              max_hp = float('-inf')
              min_hp = float('inf')
              for t in transitions[1:]: #skip first transition 
                halfperiod = (t.microseconds+(1000000*t.seconds))
                if halfperiod > max_hp: max_hp = halfperiod 
                if halfperiod < min_hp: min_hp = halfperiod 
                sumhalfperiods += halfperiod
                n += 1
              avg = float(sumhalfperiods)/float(n)
              frequency_hz = 1000000.0/ (avg * 2.0)
              stddev = 0
              for t in transitions[1:]: #skip first transition
                  stddev += pow((t.microseconds+(1000000*t.seconds)) - avg, 2)
                  
              stddev /= n-1
              stddev = math.sqrt(stddev)

              clockname = "CLOCK_" + name + "_DIV" + str(clock_divider) +  "_" + loopback_pin_name[i] + "_NANOSECONDS"
              
              logger.debug("clock {} {}, nsamples {}, min {} ns, max {} ns, avg {:.2f} ns, stddev {:.2f} ns, measured frequency = {:.0f} Hz".format(type, loopback_pin_name[i], n, min_hp*1000.0, max_hp*1000.0, avg*1000.0, stddev*1000.0,  frequency_hz))
            
            
            d[clockname] = [n, min_hp*1000.0, max_hp*1000.0, avg*1000.0, stddev*1000.0]
            pbar.update()
            '''

        for clock_divider in [10, 16]:
          for i in range(2,12):
            res = moduleTC.module.WriteSetting("FEETestEnable_" + type, 1 << i) #1 --> clock 0 --> high
            logger.debug("test enable " + type + " result: " + str(res))
            res = moduleTC.module.WriteSetting("FEETestSelect_" + type, 1 << i) #1 --> clock 0 --> high
            logger.debug("test select " + type + " result: " + str(res))
            res = moduleTC.module.WriteSetting("FEE_Clock_" + type, clock_divider) #maximum is 0x1F or 31
            logger.debug("clock for " + type + " result: "  + str(res))

            logger.debug("{}: setting clock speed of pin {} to {:.1f} Hz".format(type, bit_name[i], 1/(2.0*(8.0e-9)*float(1 << clock_divider))))
            pin_name, nsamples, min_halfperiod, max_halfperiod, avg, stddev= bobinstance.test_clock(bit_name[i])

            #if clock_divider == 10 and type == "Aux" and (bit_name[i] == "MOSI_MUSIC" or bit_name[i] == "SMART_SPI_CLK" or bit_name[i] == "SMART_SPI_RES"):
            #              input("Press a key to continue:") ##to test broken lines

            #calibrated time    t = (x+b)*a

            clockname = "CLOCK_" + name + "_DIV" + str(clock_divider) +  "_" + pin_name
            clockname_raw = clockname + "_RAW"
            clockname_calibrated = clockname + "_CALIBRATED_NANOSECONDS"
            d[clockname_raw] = [int(nsamples), int(min_halfperiod), int(max_halfperiod), float(avg), float(stddev)]
            logger.debug("calibrated half period = {:.1f} ns, frequency: {:.1f} Hz".format(a*(float(avg)+b), 1e9/(2.0*a*(float(avg)+b))))

            #note! the stddev does not get the additive term b after the linear transform! 
            d[clockname_calibrated] = [int(nsamples), a*(float(min_halfperiod) + b), a*(float(max_halfperiod)+b), a*(float(avg)+b), a*(float(stddev))] 
            logger.debug("GOT ----> {} nsamples {} min {:.1f} cycles, max {:.1f} cycles, avg {:.1f} cycles, stddev {:.1f} cycles".format(pin_name, int(nsamples), float(min_halfperiod), float(max_halfperiod), float(avg), float(stddev)))
            logger.debug("GOT ----> {} nsamples {} min {:.1f} ns, max {:.1f} ns, avg {:.1f} ns, stddev {:.1f} ns".format(pin_name, int(nsamples), a*(float(min_halfperiod) + b), a*(float(max_halfperiod)+b), a*(float(avg)+b), a*(float(stddev))))
            pbar.update()

    pbar.close()
    manager.stop()


    title = "voltages"
    filename = title + ".yaml"
    outfile = outdir + "/" + filename
    logger.log(logger.TEST_LEVEL_INFO, "Writing output to, directory {0}, filename {1}"
               .format(outdir, filename))

    with open(outfile,"w") as fptr:
         fptr.write(yaml.dump(d, default_flow_style=False))

    return



def generate_ped(fname, force=False):
    logger.log(logger.TEST_LEVEL_INFO, "Generating pedestal calibration file...")
    tmp_fname, ext = os.path.splitext(fname)
    new_ext = ".tcal"

    if tmp_fname.find("_r0")>=0:
        outfname = tmp_fname.replace("_r0","_peddb")+new_ext
    elif tmp_fname.split("/")[-1].startswith("r0"):
        toks = tmp_fname.split("/")
        path = "/".join(toks[:-1])+"/"
        outfname = path+toks[-1].replace("r0","peddb",1)+new_ext
    else:
        outfname = tmp_fname+"_peddb"+new_ext

    if force or not os.path.exists(outfname):
        cmd = "generate_ped -i {0} -o {1} -d".format(fname, outfname)
        logger.info(cmd)
        os.system(cmd)
    logger.log(logger.TEST_LEVEL_INFO, "Generated pedestal calibration: {0}"
               .format(outfname))
    return outfname

def apply_calibration(fname, pedfname, force=False):
    logger.log(logger.TEST_LEVEL_INFO, "Applying calibration...")
    if fname.find("_r0")>=0:
        outfname = fname.replace("_r0","_r1")
    elif fname.split("/")[-1].startswith("r0"):
        toks = fname.split("/")
        path = "/".join(toks[:-1])+"/"
        outfname = path+toks[-1].replace("r0","r1",1)
    else:
        tmp, ext = os.path.splitext(fname)
        outfname = tmp+"_r1"+ext
    if force or not os.path.exists(outfname):
        cmd = "apply_calibration -i {0} -p {1} -o {2}".format(fname, pedfname, outfname)
        logger.info(cmd)
        result = os.system(cmd)
        if (result != 0): raise ValueError("Could not open {0}, (did you forget to enable datataking?)".format(fname))
    return outfname


class Waveform:
    def __init__(self, fname=None):
        self.isR1 = False
        self.filename = None
        self.reader = None
        self.n_pixels = 0
        self.n_samples = 0
        #self.n_events = 0
        self.first_cell_ids = None ## shape is (n_events)
        self.stale_bit = None ## shape is (n_events)
        self.waveforms = None ## shape is (n_events, n_pixels, n_samples)
        if fname is not None:
            self.read_data(fname)

    @property
    def n_events(self):
        if self.waveforms is not None:
            return self.waveforms.shape[0]
        else:
            return 0
#    @property
#    def n_pixels(self):
#        if self.waveforms:
#            return self.waveforms.shape[1]
#        else:
#            return 0
#    @property
#    def n_samples(self):
#        if self.waveforms:
#            return self.waveforms.shape[2]
#        else:
#            return 0
    
    def read_data(self, filename):
        self.filename = filename
        self.reader = target_io.WaveformArrayReader(filename)
        self.isR1 = self.reader.fR1
        self.n_pixels = self.reader.fNPixels
        self.n_samples = self.reader.fNSamples
        n_events = self.reader.fNEvents
        self.first_cell_ids = np.zeros(n_events,dtype=np.uint16)
        self.stale_bit = np.zeros(n_events, dtype=bool) ## data format to be checked
        #Generate the memory to be filled in-place
        if self.isR1:
            self.waveforms = np.zeros((n_events,self.n_pixels, self.n_samples), dtype=np.float32)
            #for event_index in tqdm(range(0,n_events)):
            for event_index in range(0,n_events):
                #self.reader.GetR1Event(event_index,self.waveforms[event_index],self.first_cell_ids[event_index])
                #_first_cell_id, _stale, _missing_packets, _tack, _cpu_s, _cpu_ns = self.reader.GetR1Event(event_index,self.waveforms[event_index])
                self.first_cell_ids[event_index], self.stale_bit[event_index], _missing_packets, _tack, _cpu_s, _cpu_ns = self.reader.GetR1Event(event_index,self.waveforms[event_index])
            #self.reader.GetR1Events(0,self.waveforms,self.first_cell_ids)
        else:
            self.waveforms = np.zeros((n_events,self.n_pixels, self.n_samples),dtype=np.ushort)   #needed for R0 data
            #for event_index in tqdm(range(0,n_events)):
            for event_index in range(0,n_events):
                #self.reader.GetR0Event(event_index,self.waveforms[event_index],self.first_cell_ids[event_index])
                self.first_cell_ids[event_index], self.stale_bit[event_index], _missing_packets, _tack, _cpu_s, _cpu_ns = self.reader.GetR0Event(event_index,self.waveforms[event_index])
                #current_cpu_ns = self.reader.fCurrentTimeNs
                #current_cpu_s = self.reader.fCurrentTimeSec
                #tack_timestamp = self.reader.fCurrentTimeTack
                #cpu_timestamp = ((current_cpu_s * 1E9) + np.int64(current_cpu_ns))/1000000
                #have the cpu timestamp in some nice format
                #t_cpu = pd.to_datetime(np.int64(current_cpu_s * 1E9) + np.int64(current_cpu_ns),unit='ns')
                                
        #print ("Stale events detected: ", np.where(self.stale_bit)[0])
        #np.savetxt("stale_list.txt",a)

    def subtract_baseline(self, t_bsl=10):
        self.bsls = np.mean(self.waveforms[:,:,:t_bsl], axis=2)
        self.waveforms -= self.bsls[:,:,np.newaxis]

    def filter_events_by_fci(self, fci_min=0, fci_max=16384):
        idx = np.where( np.logical_or(self.first_cell_ids<fci_min, self.first_cell_ids>fci_max))
        self.waveforms = self.waveforms[idx]
        self.first_cell_ids = self.first_cell_ids[idx]
        #self.n_events = len(self.waveforms)

    def filter_events_by_stale(self):
        self.waveforms = self.waveforms[np.logical_not(self.stale_bit)]
        #self.n_events = len(self.waveforms)

class Pedestal:
    def __init__(self):
        self.pedmap = None
        self.hitmap = None
        self.stddevmap = None
        self.nmodules = 1
        self.n_max_block = 512 #128
        self.n_blocks = None
                
    def read_from_database(self, fname):
        ped = target_calib.PedestalArrayReader(fname)
        self.pedmap = np.array(ped.GetPedestal()[0]) ## only module 0
        try:
            self.hitmap = np.array(ped.GetHits()[0]) ## only module 0
        except:
            logger.warning("No hit map found.")
            self.hitmap = None
        try:
            self.stddevmap = np.array(ped.GetStdDev()[0]) ## only module 0
        except:
            logger.warning("No stddev map found.")
            self.stddevmap = None
        #self.n_blocks = int((len(self.pedmap[0][0])-31)/32)
        self.n_blocks = int((self.pedmap.shape[-1]-31)/32)

    def calculate_from_waveforms(self, wf=None, fname=None, diagnostic=False ):
        if wf is None:
            if fname is None:
                raise ValueError("Please provide waveforms or filename")
            else:
                wf = Waveform(fname)
        if wf.isR1:
            raise ValueError("Waveforms are not R0 events. Please provide R0 events")

        self.n_pixels = wf.n_pixels
        self.n_samples = wf.n_samples
        self.n_samples_ped = self.n_samples+31
        self.pedmaker = target_calib.PedestalMaker(self.nmodules,self.n_max_block,wf.n_samples,False)
        #self.pedmaker = target_calib.PedestalMaker(self.nmodules,self.n_max_block,wf.n_samples,diagnostic) ## to be tested with new TargetCalib
        for ev in range(wf.n_events):
            self.pedmaker.AddEvent(wf.waveforms[ev,:,:],wf.first_cell_ids[ev,:])

        self.pedmap = np.array(self.pedmaker.GetPed()[0]) ## only module 0
        if True: #diagnostic:
            hits = self.pedmaker.GetHits()
            self.hitmap = np.array(hits[0]) ## only module 0
            #stddev = self.pedmaker.GetStd()  ## to be tested with new TargetCalib
            #self.stddevmap = np.array(stddev[0]) ## only module 0 ## to be tested with new TargetCalib
        self.n_blocks = int((self.pedmap.shape[-1]-31)/32)

    def save_to_file(self,outname):
        self.pedmaker.Save(outname, False)


