#!/usr/bin/env python

import time
import sys
import math
import numpy as np
from MyLogging import logger
import enlighten


WR = 0b101
RD = 0b100


pix_to_smart_channel = [1,5,3,7,9,13,11,15,0,4,2,6,8,12,10,14]
def pix_to_ch_list(pixel_list=None):
    if pixel_list is None:
        return None
    else:
        chlist = []
        for pix in pixel_list:
            asic = int(pix/self.NCH)
            ipix = pix%self.NCH
            chlist.append(asic*self.NCH+pix_to_smart_channel[ipix])
        return chlist
    

class SMART:
    WR = 0b101
    RD = 0b100
    NREG=25
    MUX_ADD=24
    ADC_ADD=25
    DUMMY_ADD = 17
    NCH=16
    NASIC=4
    CHLIST = [i for i in range(NCH)]
    CHLISTALL = [i for i in range(NCH*NASIC)]
    DACMAX= 1<<8 # 8-bit register
    EN1_ADD = 18
    EN2_ADD = 19
    EN3_ADD = 20
    R_ADD = 21
    C_ADD = 22
    PZ_ADD = 23

    def __init__(self, module):
        #self.WR = 0b101
        #self.RD = 0b100
        self.module = module.module
        self.moduleTC = module

    def _ch_list_to_mask(self, chlist):
        channel_mask = sum([1<<i for i in chlist])
        return channel_mask
                
        
    def write_register(self,ireg, vals, asics=0xf, readback=False):
        self.enable(asics=asics)
        if type(vals) is not list:
            vals = [vals]*self.NASIC
        for i,val in enumerate(vals):
            self.module.WriteSetting("SMART_WriteData"+str(i),val)
        #self.module.WriteSetting("SMART_WriteData0",val)
        #self.module.WriteSetting("SMART_WriteData1",val)
        #self.module.WriteSetting("SMART_WriteData2",val)
        #self.module.WriteSetting("SMART_WriteData3",val)
        self.module.WriteSetting("SMART_Address", self.WR << 5 | ireg)
        #self.module.WriteSetting("SMART_Start",0)
        self.module.WriteSetting("SMART_Start",1)
        time.sleep(0.1)
        #print(module.ReadSetting("SMART_Valid"))
        self.module.WriteSetting("SMART_Start",0)
        val0 = self.module.ReadSetting("SMART_WriteData0")[1]
        val1 = self.module.ReadSetting("SMART_WriteData1")[1]
        val2 = self.module.ReadSetting("SMART_WriteData2")[1]
        val3 = self.module.ReadSetting("SMART_WriteData3")[1]
        logger.debug("Data written on register {0}: {1},{2},{3},{4}".format(ireg,val0,val1,val2,val3))
        self.enable(asics=0xf)
        if readback:
            vals = self.read_register(ireg)
            for i in range(self.NASIC):
                if (asics >> i) & 0b1 and vals[i] != val:
                    logger.error("ERROR in SMART write_register(): data read from register "
                                 +str(ireg)+" of SMART "+str(i)+" does not match written data.")
                    
        return

    def read_register(self,ireg):
        self.module.WriteSetting("SMART_Address", self.RD << 5 | ireg)
        #self.module.WriteSetting("SMART_Start",0)
        self.module.WriteSetting("SMART_Start",1)
        time.sleep(0.1)
        valid = self.module.ReadSetting("SMART_Valid")[1]
        self.module.WriteSetting("SMART_Start",0)
        #time.sleep(0.5)
        if valid!=1:
            raise Exception("Data read from SMART is not valid.")
        val0 = self.module.ReadSetting("SMART_ReadData0")[1]
        val1 = self.module.ReadSetting("SMART_ReadData1")[1]
        val2 = self.module.ReadSetting("SMART_ReadData2")[1]
        val3 = self.module.ReadSetting("SMART_ReadData3")[1]
        logger.debug("Data read from register {0}: {1},{2},{3},{4}".format(ireg,val0,val1,val2,val3))

        return val0, val1, val2, val3


    def reset(self, asics=0xf):
        self.module.WriteSetting("SMART_Reset",asics)
        time.sleep(0.1)
        self.module.WriteSetting("SMART_Reset",0x0)
        return

    def enable(self, asics=0xf):
        self.module.WriteSetting("SMART_Enable",asics)
        return

    #def enable_channels(self, channel_mask=0xffff,asics=0xf): ## must a 16-bit number. ex: 0xffff enable all channels, 0x000f enables channels 0-1-2-3
    def enable_channels(self, channel_list=CHLIST,asics=0xf): 
        channel_mask = self._ch_list_to_mask(channel_list)
        mask1 = channel_mask & 0xff
        mask2 = channel_mask>>8 & 0xff
        ireg1 = self.EN1_ADD
        ireg2 = self.EN2_ADD
        self.write_register(ireg1, mask1, asics=asics, readback=True)
        time.sleep(0.1)
        self.write_register(ireg2, mask2, asics=asics, readback=True)
        time.sleep(0.1)
        return

    def enable_channels64(self, channel_list=CHLISTALL): # chlist goes from 0 to 63
        for i in range(self.NASIC):
            chlist = [ch for ch in self.CHLIST if ch+i*self.NCH in channel_list]
            asic_mask = 1<<i
            self.enable_channels(channel_list=chlist, asics=asic_mask)
        return
    
    def disable_channels64(self, channel_list=None):
        if channel_list is None:
            channel_list = []
        for i in range(self.NASIC):
            chlist = [ch for ch in self.CHLIST if ch+i*self.NCH not in channel_list]
            asic_mask = 1<<i
            self.enable_channels(channel_list=chlist, asics=asic_mask)
        return

    def enable_pixels64(self, pixel_list=CHLISTALL):
        chlist = pix_to_ch_list(pixel_list=pixel_list)
        return self.enable_channels64(channel_list=chlist)

    def disable_pixels64(self, pixel_list=None):
        chlist = pix_to_ch_list(pixel_list=pixel_list)
        return self.disable_channels64(channel_list=chlist)

    def set_dac(self, channel_list=CHLIST, vals=100, asics=0xf):
        if type(vals) is not list:
            vals = [vals]*len(channel_list)
        elif len(vals)!=len(channel_list):
            raise ValueError("SMART_utils::set_dac : cannot set SMART DAC values. Please provide a list with length "+str( len(channel_list))+".")
        for i in channel_list:
            self.write_register(i,vals[i], asics=asics, readback=True)
            time.sleep(0.1)
        return

    def config_global(self,r=0,c=0,pz=63, asics=0xf):
        self.write_register(self.R_ADD, r, asics=asics, readback=True)
        self.write_register(self.C_ADD, c, asics=asics, readback=True)
        self.write_register(self.PZ_ADD, pz, asics=asics, readback=True)
        return
    
    def init_smart(self, channel_list=CHLIST, dac_vals=100, global_vals=[0,0,63], asics=0xf):
        self.enable_channels(channel_list=channel_list, asics=asics)
        self.write_register(self.EN3_ADD, 255, asics=0xf, readback=False)

        self.set_dac(channel_list=channel_list, vals=dac_vals, asics=asics)
        self.config_global(r=global_vals[0], c=global_vals[1], pz=global_vals[2], asics=asics)
     
        return

    def read_adc(self,channel=None, calib=None, asics=0xf, verbose=False):
        if channel is not None:
            self.write_register(self.MUX_ADD, channel, asics=asics, readback=True)
        if calib is not None:
            if type(calib) is not list:
                calib = [calib]*self.NASIC
            self.write_register(self.DUMMY_ADD, calib, asics=asics, readback=True)
        self.module.WriteSetting("SMART_Address", self.RD << 5 | self.ADC_ADD)
        self.module.WriteSetting("SMART_Start",1)
        #time.sleep(0.01)
        valid = self.module.ReadSetting("SMART_Valid")[1]
        self.module.WriteSetting("SMART_Start",0)
        #time.sleep(0.5)
        if valid!=1:
            raise Exception("ADC Data read from SMART is not valid.")
        val0 = self.module.ReadSetting("SMART_ADCData0")[1]
        val1 = self.module.ReadSetting("SMART_ADCData1")[1]
        val2 = self.module.ReadSetting("SMART_ADCData2")[1]
        val3 = self.module.ReadSetting("SMART_ADCData3")[1]
        if verbose:
            if channel is None:
                logger.debug("ADC data read: {0},{1},{2},{3}".format(val0,val1,val2,val3))
            else:
                logger.debug("ADC data read from channel {0}: {1},{2},{3},{4}".format(channel,val0,val1,val2,val3))

        return val0, val1, val2, val3

    def read_adc_mean(self,channel=None, calib=None, asics=0xf, nsamp=50):
        if channel is not None:
            self.write_register(self.MUX_ADD, channel, asics=asics, readback=True)
        if calib is not None:
            if type(calib) is not list:
                calib = [calib]*self.NASIC
            self.write_register(self.DUMMY_ADD, calib, asics=asics, readback=True)
        values_ADC = []
        for i in range(nsamp):
            xxx = self.read_adc(channel=None, calib=None, asics=asics, verbose=False)
            values_ADC.append(list(xxx))
        values_ADC = np.array(values_ADC)
        ADC_mean = np.mean(values_ADC, axis=0)
        ADC_sigma = np.std(values_ADC, axis=0)
        return ADC_mean, ADC_sigma


    def calib_adc(self, asics=0xf, full_output=False):
        allADCval_mean = np.zeros((self.NASIC*self.NCH, self.DACMAX))
        allADCval_sigma = np.zeros((self.NASIC*self.NCH, self.DACMAX))
        calib_vals = np.zeros(self.NASIC*self.NCH)
        manager = enlighten.get_manager()
        pbar = manager.counter(total=self.NCH*self.DACMAX, desc='SMART channel calibration', leave = False)

        for i in range(self.NCH):
            logger.info("Calibrating SMART channel "+str(i))
            for j in range(0,self.DACMAX): ## loop on dummy channel 17
                pbar.update()
                if j%50==0:
                    #logger.debug("DAC17="+str(j))
                    pass
                self.write_register(self.DUMMY_ADD, j, asics=asics)
                mu,sigma = self.read_adc_mean(channel=i,calib=None, asics=asics, nsamp=10)
                allADCval_mean[i::self.NCH,j] = mu
                allADCval_sigma[i::self.NCH,j] = sigma
            ## get calib val
            for k in range(self.NASIC):
                _c = np.where(allADCval_mean[i::self.NCH][k]>0)[0]
                if len(_c)>0:
                    calib_vals[i+k*self.NCH] = _c[0]
                else:
                    calib_vals[i+k*self.NCH] = -1
        pbar.close()
        manager.stop()

        if full_output:
            out = calib_vals, allADCval_mean, allADCval_sigma
        else:
            out = calib_vals
        return out




### OLD METHODS
def write_register(module,ireg, val):
    module.WriteSetting("SMART_WriteData0",val)
    module.WriteSetting("SMART_WriteData1",val)
    module.WriteSetting("SMART_WriteData2",val)
    module.WriteSetting("SMART_WriteData3",val)
    module.WriteSetting("SMART_Address", WR << 5 | ireg)
    module.WriteSetting("SMART_Start",1)
    time.sleep(0.5)
    #print(module.ReadSetting("SMART_Valid"))
    module.WriteSetting("SMART_Start",0)
    print("data to be written:")
    print(module.ReadSetting("SMART_WriteData0"))
    print(module.ReadSetting("SMART_WriteData1"))
    print(module.ReadSetting("SMART_WriteData2"))
    print(module.ReadSetting("SMART_WriteData3"))
    return

def read_register(module,ireg):
    module.WriteSetting("SMART_Address", RD << 5 | ireg)
    module.WriteSetting("SMART_Start",1)
    time.sleep(0.5)
    print(module.ReadSetting("SMART_Valid"))
    module.WriteSetting("SMART_Start",0)
    time.sleep(0.5)
    val0 = module.ReadSetting("SMART_ReadData0")[1]
    val1 = module.ReadSetting("SMART_ReadData1")[1]
    val2 = module.ReadSetting("SMART_ReadData2")[1]
    val3 = module.ReadSetting("SMART_ReadData3")[1]
    return val0, val1, val2, val3


def reset_smart(module):
    module.WriteSetting("SMART_Reset",0xf)
    time.sleep(0.1)
    module.WriteSetting("SMART_Reset",0x0)
    return

def enable_smart(module, asics=0xf):
    module.WriteSetting("SMART_Enable",asics)
    return

def program_smart(module):
    ireg=18
    val=255
    write_register(module,ireg, val)
    time.sleep(0.1)
    print("Reading reg:",ireg,read_register(module,ireg))
    time.sleep(0.1)

    ireg=19
    val=255
    write_register(module,ireg, val)
    time.sleep(0.1)
    print("Reading reg:",ireg,read_register(module,ireg))
    time.sleep(0.1)


    ## disable one channel
    enable_smart(module, asics=0b0000)
    ireg=18
    val=255
    write_register(module,ireg, val)
    time.sleep(0.1)
    print("Reading reg:",ireg,read_register(module,ireg))
    time.sleep(0.1)
    enable_smart(module, asics=0xf)
    ########

    
    val=100
    for i in range(16):
        print("At channel", i)
        write_register(module,i,val+0*i)
        time.sleep(0.1)
        print("Reading channel", i)
        print(read_register(module,i))
        time.sleep(0.1)

    ireg=21
    val=0
    write_register(module,ireg, val)
    time.sleep(0.1)
    ireg=22
    val=0
    write_register(module,ireg, val)
    time.sleep(0.1)
    ireg=23
    val=40
    write_register(module,ireg, val)
    time.sleep(0.1)
      
    return
