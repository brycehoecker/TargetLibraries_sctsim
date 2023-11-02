#!/usr/bin/env python

import serial
import serial.tools.list_ports
import time
import sys
import math
import termios #for setting HUPCL
#from mylogger import *
#sys.tracebacklimit=0

#loglevel=999
from MyLogging import logger


class Arduino:
  def __init__(self, serialport_name=None, ard_id=None):
    self.ard_id = ard_id ## to be updated if None
    if serialport_name is None:
      if ard_id is None:
        raise ValueError("Please provide either serialport or arduino id to initialize serial connection")
      serialport_name = get_usbport(ard_id)
      if serialport_name is None:
        logger.error("Cannot detect arduino with ID "+str(ard_id))

    self.sleep_retry = 2 #seconds
    self.max_retries = 5
    self.ser = None
    self.is_open=False
    if serialport_name:
      self.ser = ser = serial.Serial()
      self.ser.port = serialport_name
      self.ser.baudrate = 115200
      self.ser.bytesize = serial.EIGHTBITS
      self.ser.parity = serial.PARITY_NONE
      self.ser.stopbits = serial.STOPBITS_ONE
      self.ser.timeout = 1
      self.sleep1=0.1
      #self.ser.setDTR(1)

      self.ser.open()
      self.is_open = self.ser.is_open
      
      if not self.ser.is_open:
        logger.error("Could not open serial port "+serialport_name)
      else:
        if self.ard_id is None:
          self.ard_id = self.get_id()
      
  def __del__(self):
    if self.ser:
      self.ser.flush()
      self.ser.close()


  def send(self, str):
    msg = str + "\n" #append newline
    logger.debug("Sending: \"" + str + "\"" )
    self.ser.write(msg.encode())

  def read(self):
    msg = self.ser.read_until()
    return msg.decode().rstrip('\n\r')


  ## eventually add function send_and_check with retries
  
  def get_id(self):
    self.send("ID")
    msg= self.read()
    return msg
  ## add a function to check if resource is still available
  
  def check_int(self, cmp):
    msg_raw = self.ser.read_until()
    msg = msg_raw.decode().rstrip('\n')
    logger.debug("Checking response: expected \"{}\", got \"{}\".".format(cmp, msg.rstrip('\n')))
    if msg == "":
      logger.critical("No message recevied from the arduino "+self.ard_id+", is the device on and connected?");
      exit (1)
    a = int(msg)
    if cmp == a:
      return 0
    else:
      logger.critical("Check failed, expected \"{}\", got \"{}\".".format(cmp, msg.decode().rstrip('\n')))
      return 1


  def check_float(self, cmp):
    msg = self.ser.read_until()
    logger.debug("Checking response, expected \"{}\", got \"{}\".".format(cmp, msg.decode().rstrip('\n')))
    try:
      a = float(msg)
      cmp2 = float(cmp)
    except:
      raise Exception("Could not convert string into float")
    if math.isclose(a, cmp2, rel_tol=1e-5):
      return 0
    else:
      logger.critical("Check failed, expected \"{}\", got \"{}\".".format(cmp, msg.decode().rstrip('\n')))
      return 1

  def check_string(self, cmp):
      msg = self.ser.read_until().decode().strip()#rstrip('\n\r')
      if cmp == msg:
          return 0
      else:
          raise Exception("Check failed, expected \"{}\", got \"{}\".".format(cmp, msg.rstrip('\n')))
          return 1


class ArduinoTBOB(Arduino):
  def __init__(self, serialport_name=None, ard_id=None):
    super().__init__(serialport_name=serialport_name, ard_id=ard_id)

  def setmux(self, group):
    max_retries = 5
    success = False
    for i in range(max_retries):
      self.send(str(group))
      time.sleep(0.5)
      ## check if it is ok
      if self.check_string("ACK "+str(group))!=0:
        logger.error("Could not send arduino command.")
      else:
        success = True
        break
    if not success:
      raise Exception("Error while setting trigger MUX")






class ArduinoSBOB(Arduino):


  #calibration
  #HV power supply: 31.4 V
  #sbob 1, measured on R70 (HV1): 30.7 V (some voltage drop along channels)
  #sbob 1, measured on R61 (HV2): 30.7 V (some voltage drop along channels)
  #sbob 2, measured on R70 (HV1): 30.7 V (some voltage drop along channels)
  #sbob 2, measured on R61 (HV2): 30.7 V (some voltage drop along channels)
  #sbob 1, measured on R37 (3V3A): 3.26 V
  #sbob 1, measured on R35 (3V3B): 3.26 V
  #sbob 2, measured on R37 (3V3A): 3.27 V
  #sbob 2, measured on R35 (3V3B): 3.25 V
  #sbob 1, measured on R55 (5V0A): 4.93 V
  #sbob 1, measured on R56 (5V0B): 4.93 V
  #sbob 2, measured on R55 (5V0A): 4.93 V
  #sbob 2, measured on R56 (5V0B): 4.93 V
  #sbob 1, measured raw value HV1: 431 adc units
  #sbob 1, measured raw value HV2: 431 adc units
  #sbob 2, measured raw value HV1: 433 adc units
  #sbob 2, measured raw value HV1: 432 adc units
  #sbob 1, measured raw value 3V3A: 689 adc units
  #sbob 1, measured raw value 3V3B: 689 adc units
  #sbob 2, measured raw value 3V3A: 688 adc units
  #sbob 2, measured raw value 3V3B: 691 adc units
  #sbob 1, measured raw value 5V0A: 685 adc units
  #sbob 1, measured raw value 5V0B: 684 adc units
  #sbob 2, measured raw value 5V0A: 685 adc units
  #sbob 2, measured raw value 5V0B: 685 adc units
  #calibration value sbob1 HV1: 30.7V / 431 = 0.0712
  #calibration value sbob1 HV2: 30.7V / 431 = 0.0712
  #calibration value sbob2 HV1: 30.7V / 433 = 0.0709
  #calibration value sbob2 HV2: 30.7V / 432 = 0.0711
  #calibration value sbob1 3V3A: 3.26V / 689 = 0.00473
  #calibration value sbob1 3V3B: 3.26V / 689 = 0.00473
  #calibration value sbob2 3V3A: 3.27V / 688 = 0.00474
  #calibration value sbob2 3V3B: 3.25V / 691 = 0.00474
  #calibration value sbob1 5V0A: 4.93V / 685 = 0.00720
  #calibration value sbob1 5V0B: 4.93V / 684 = 0.00721
  #calibration value sbob2 5V0A: 4.93V / 685 = 0.00720
  #calibration value sbob2 5V0B: 4.93V / 685 = 0.00720
  HV_CALIB_MULT_SBOB1_HV1 = 0.0712
  HV_CALIB_MULT_SBOB1_HV2 = 0.0712
  HV_CALIB_MULT_SBOB2_HV1 = 0.0709
  HV_CALIB_MULT_SBOB2_HV2 = 0.0711


  HV_CALIB_MULT_SBOB1_3V3A = 0.00473
  HV_CALIB_MULT_SBOB1_3V3B = 0.00473
  HV_CALIB_MULT_SBOB2_3V3A = 0.00474
  HV_CALIB_MULT_SBOB2_3V3B = 0.00474

  HV_CALIB_MULT_SBOB1_5V0A = 0.00720
  HV_CALIB_MULT_SBOB1_5V0B = 0.00721
  HV_CALIB_MULT_SBOB2_5V0A = 0.00720
  HV_CALIB_MULT_SBOB2_5V0B = 0.00720



  def __init__(self, serialport_name=None, ard_id=None):
    super().__init__(serialport_name=serialport_name, ard_id=ard_id)

  def read_hv(self, k, calibrated=True): ## 1, 2


    if k not in [1,2]:
      raise ValueError("Invalid value for HV reading")
    self.send("HV"+str(k))
    msg = self.read()
    ## decode here msg and convert to HV value
    meas_raw = int(msg.split()[1])
    if (calibrated):
      if self.ard_id == "BOB1" and k==1:
        meas = float(meas_raw) * self.HV_CALIB_MULT_SBOB1_HV1
      elif self.ard_id == "BOB1" and k==2:
        meas = float(meas_raw) * self.HV_CALIB_MULT_SBOB1_HV2
      elif self.ard_id == "BOB2" and k==1:
        meas = float(meas_raw) * self.HV_CALIB_MULT_SBOB2_HV1
      elif self.ard_id == "BOB2" and k==2:
        meas = float(meas_raw) * self.HV_CALIB_MULT_SBOB2_HV2
      else:
        logger.error("Could not identify arduino id while reading calibrated HV voltage")
      meas= round(meas,2)
    return meas, meas_raw

  def read_voltage(self, lvl, calibrated=True): #lvl="3V3A", "3V3B", "5V0A", "5V0B"

    if lvl not in ["3V3A", "3V3B", "5V0A", "5V0B"]:
      raise ValueError("Invalid identifier for power supply voltage")
    self.send(lvl)
    msg = self.read()
    meas_raw = int(msg.split()[1])
    if (calibrated):
      if self.ard_id == "BOB1" and lvl=="3V3A":
        meas = float(meas_raw) * self.HV_CALIB_MULT_SBOB1_3V3A
      elif self.ard_id == "BOB1" and lvl=="3V3B":
        meas = float(meas_raw) * self.HV_CALIB_MULT_SBOB1_3V3B
      elif self.ard_id == "BOB2" and lvl=="3V3A":
        meas = float(meas_raw) * self.HV_CALIB_MULT_SBOB2_3V3A
      elif self.ard_id == "BOB2" and lvl=="3V3B":
        meas = float(meas_raw) * self.HV_CALIB_MULT_SBOB2_3V3B
      elif self.ard_id == "BOB1" and lvl=="5V0A":
        meas = float(meas_raw) * self.HV_CALIB_MULT_SBOB1_5V0A
      elif self.ard_id == "BOB1" and lvl=="5V0B":
        meas = float(meas_raw) * self.HV_CALIB_MULT_SBOB1_5V0B
      elif self.ard_id == "BOB2" and lvl=="5V0A":
        meas = float(meas_raw) * self.HV_CALIB_MULT_SBOB2_5V0A
      elif self.ard_id == "BOB2" and lvl=="5V0B":
        meas = float(meas_raw) * self.HV_CALIB_MULT_SBOB2_5V0B
      else:
        logger.error("Could not identify arduino id while reading calibrated voltage level for power (3.3V, 5V)")
      meas= round(meas,2)
    return meas, meas_raw


  def read_logic(self, lvl):
    if lvl not in ["SMART_SPI_CLK", "SMART_SPI_RES", "MOSI_MUSIC", "MISO_MUSIC", "SCLK_MUSIC", "RESET_MUSIC", "SS_MUSIC0", "SS_MUSIC1", "SS_MUSIC2", "SS_MUSIC3"]:
      raise ValueError("Invalid identifier for logic level")
    self.send(lvl)
    msg = self.read()
    meas = int(msg.split()[1])
    return meas

  def test_clock(self, lvl):
    if lvl not in ["SMART_SPI_CLK", "SMART_SPI_RES", "MOSI_MUSIC", "MISO_MUSIC", "SCLK_MUSIC", "RESET_MUSIC", "SS_MUSIC0", "SS_MUSIC1", "SS_MUSIC2", "SS_MUSIC3"]:
      raise ValueError("Invalid identifier for logic level")
    message = "CLOCK " + lvl
    self.send(message)
    logger.debug("sending: " + message)
    msg = self.read()
    logger.debug("received = " + msg)

    time.sleep(1)
    self.send("CLOCK_RESULTS_SHORT")
    msg = self.read()
    logger.debug("received = " + msg)

    split = msg.split()
    #TODO check that split has exaclty 5 itmes
    return split[0], split[1], split[2], split[3], split[4], split[5]


def get_usbport(ard_id): ## valid values are BOB1, BOB2, TBOB
  portlist_all = [comport.device for comport in serial.tools.list_ports.comports()] 
  portlist = [ p for p in portlist_all if "USB" in p]
  sleep_retry = 2 #seconds
  max_retries = 5
  for portname in portlist:

    #prevent arduino autoreset on DTR
    #https://raspberrypi.stackexchange.com/questions/9695/disable-dtr-on-ttyusb0/31298#31298
    f = open(portname)
    attrs = termios.tcgetattr(f)
    attrs[2] = attrs[2] & ~termios.HUPCL
    termios.tcsetattr(f, termios.TCSAFLUSH, attrs)
    f.close()


    ard = Arduino(portname)
    for i in range(max_retries):
      ard.send("ID")
      msg = ard.read()
      if msg:
        break
      time.sleep(sleep_retry)
    if msg==ard_id:
      return portname
  return None
