#!/usr/bin/env python
import time
import os,sys
import argparse
import yaml

from utils import *
from MyLogging import logger

import avrcmd
import avrframe
from peltcmd import PeltierCmd
from peltcmd import cmd_response
from peltcmd import hex_byte
import struct

def sendcmd_peltier(avr,cmd,opcode,write=False, parameter=None, result=None):
    timeout = 1
    cmd.opcode(opcode, write)
    if parameter is None:
        parameter = 0
    if parameter is not None:
        if not write:
            logger.warning('Peltier command: Parameter Supplied, but write bit not set...')
        cmd.param(parameter)

    msg_to_send = cmd.msg()
    logger.debug(cmd)
    frame_to_send = avrframe.frame(msg_to_send)
    logger.debug('avrframe bytes: {}'.format(' '.join([hex_byte(b) for b in frame_to_send])))
    tlm_msg = cmd_response(avr, frame_to_send, timeout=timeout)
    if tlm_msg is not None:
        logger.debug(tlm_msg)
        if len(tlm_msg.params) == 4:
            ret2 = '->Param (uint32): {}\n->Param  (float): {}\n'
            ipar = struct.unpack('!L', bytearray(tlm_msg.params))[0]
            fpar = struct.unpack('!f', bytearray(tlm_msg.params))[0]
            ret2 = ret2.format(ipar, fpar)
            logger.debug(ret2)
            if result=='float':
                return fpar
            elif result=='int':
                return ipar
            else:
                return None
    return None


def do_peltier(outdir, target_host=avrcmd.HOST):
    target_port = avrcmd.PORT
    localhost = avrcmd.HOST0
    localport = avrcmd.PORT0
    #args = parser.parse_args(args=args)
    timeout = 1
    avr = avrcmd.AVRcmd(target_host, target_port,
                        localhost, localport)

    ## flush buffer
    frame_to_send = []
    try:
        tlm_msg = cmd_response(avr, frame_to_send, timeout=timeout)
    except TimeoutError:
        pass
    except:
        raise
    logger.log(logger.TEST_LEVEL_INFO, "Flushed peltier microcontroller buffer...")
        
    ## Start peltier test
    cmd = PeltierCmd(target_host)


    ## Read firmware version and date ## opcodes 0,1,2,3
    logger.log(logger.TEST_LEVEL_INFO, "Reading peltier microcontroller firmware version...")
    opcode = 0
    firm_version = sendcmd_peltier(avr,cmd,opcode,write=False, parameter=None, result='int')
    time.sleep(0.1)
    opcode = 1
    firm_year = sendcmd_peltier(avr,cmd,opcode,write=False, parameter=None, result='int')
    time.sleep(0.1)
    opcode = 2
    firm_month = sendcmd_peltier(avr,cmd,opcode,write=False, parameter=None, result='int')
    time.sleep(0.1)
    opcode = 3
    firm_day = sendcmd_peltier(avr,cmd,opcode,write=False, parameter=None, result='int')
    time.sleep(0.1)
    logger.log(logger.TEST_LEVEL_INFO, "version: {0}, date: {1}-{2}-{3}".format(firm_version, firm_year, firm_month, firm_day))
    
    ## Read temperatures ## opcode = 28,29,30,31
    logger.log(logger.TEST_LEVEL_INFO, "Reading sensor thermistors through uC...")
    opcode = 28
    temp1 = sendcmd_peltier(avr,cmd,opcode,write=False, parameter=None, result='float')
    time.sleep(0.1)
    opcode = 29
    temp2 = sendcmd_peltier(avr,cmd,opcode,write=False, parameter=None, result='float')
    time.sleep(0.1)
    opcode = 30
    temp3 = sendcmd_peltier(avr,cmd,opcode,write=False, parameter=None, result='float')
    time.sleep(0.1)
    opcode = 31
    temp4 = sendcmd_peltier(avr,cmd,opcode,write=False, parameter=None, result='float')
    time.sleep(0.1)
    
    ## turn on/off peltier and read current
    logger.log(logger.TEST_LEVEL_INFO, "Turning on/off peltier and reading absorbed current...")
    opcode,par = 32,0
    sendcmd_peltier(avr,cmd,opcode,write=True, parameter=par, result=None)
    time.sleep(2)
    opcode = 23
    pelt_curr_off = sendcmd_peltier(avr,cmd,opcode,write=False, parameter=None, result='float')
    time.sleep(0.1)
    
    opcode,par = 32,1
    sendcmd_peltier(avr,cmd,opcode,write=True, parameter=par, result=None)
    time.sleep(2)
    opcode = 23
    pelt_curr_on = sendcmd_peltier(avr,cmd,opcode,write=False, parameter=None, result='float')
    time.sleep(0.1)
    
    opcode,par = 32,0
    sendcmd_peltier(avr,cmd,opcode,write=True, parameter=par, result=None)
    time.sleep(2)
    opcode = 23
    pelt_curr_off1 = sendcmd_peltier(avr,cmd,opcode,write=False, parameter=None, result='float')
    time.sleep(0.1)
    
    d = {}
    d['Peltier_firm_version'] = firm_version
    d['Peltier_firm_year'] = firm_year
    d['Peltier_firm_month'] = firm_month
    d['Peltier_firm_day'] = firm_day
    d['Peltier_temp1'] = temp1
    d['Peltier_temp2'] = temp2
    d['Peltier_temp3'] = temp3
    d['Peltier_temp4'] = temp4
    d['Peltier_curr_off_before'] = pelt_curr_off
    d['Peltier_curr_on'] = pelt_curr_on
    d['Peltier_curr_off_after'] = pelt_curr_off1
    
    
    title = "peltier"
    filename = title + ".yaml"
    outfile = outdir + "/" + filename
    logger.log(logger.TEST_LEVEL_INFO, "Writing output to, directory {0}, filename {1}".format(outdir, filename))

    with open(outfile,"w") as fptr:
         fptr.write(yaml.dump(d, default_flow_style=False))
