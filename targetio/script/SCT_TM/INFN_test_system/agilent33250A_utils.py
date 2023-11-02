#!/usr/bin/env python

import serial
import time
import sys
import math
#from mylogger import *
#sys.tracebacklimit=0

#loglevel=999
from MyLogging import logger


class agilent33250A:
  def __init__(self, serialport_name):
    self.ser = ser = serial.Serial()
    self.ser.port = serialport_name
    self.ser.baudrate = 115200
    self.ser.bytesize = serial.EIGHTBITS
    self.ser.parity = serial.PARITY_NONE
    self.ser.stopbits = serial.STOPBITS_ONE
    self.ser.timeout = 1
    self.sleep1=0.1


    self.ser.open()

    if not ser.is_open:
            logger.critical("Could not open serial port")
            sys.exit(1)
    self.ser.flush()

  def __del__(self):
    self.ser.flush()
    self.ser.close()


  def send(self, str):
    msg = str + "\n" #append newline
    logger.debug("Sending: \"" + str + "\"" )
    self.ser.write(msg.encode())


  def check_int(self, cmp):
    msg_raw = self.ser.read_until()
    msg = msg_raw.decode().strip('\n')
    logger.debug("Checking response: expected \"{}\", got \"{}\".".format(cmp, msg.strip('\n')))
    if msg == "":
      logger.critical("No message recevied from the function generator, is the device on and connected?");
      exit (1)
    a = int(msg)
    if cmp == a:
      return 0
    else:
      logger.critical("Check failed, expected \"{}\", got \"{}\".".format(cmp, msg.strip('\n')))
      return 1


  def check_float(self, cmp):
    msg = self.ser.read_until()
    msg = msg.decode().strip('\n')
    logger.debug("Checking response, expected \"{}\", got \"{}\".".format(cmp, msg))
    try:
      a = float(msg)
      cmp2 = float(cmp)
    except:
      logger.critical("Could not convert string into float")
      return 1
    if math.isclose(a, cmp2, rel_tol=1e-5):
      return 0
    else:
      logger.critical("Check failed, expected \"{}\", got \"{}\".".format(cmp, msg))
      return 1

  def check_string(self, cmp):
      msg = self.ser.read_until().decode().strip('\n')
      if cmp == msg:
          return 0
      else:
          logger.critical("Check failed, expected \"{}\", got \"{}\".".format(cmp, msg))
          return 1



