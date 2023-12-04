#!/usr/bin/env python
from FPGAcmd import FPGAcmd
from AVRcmd import AVRcmd
from time import sleep

__author__ = "Sterling Peet"
__author_email__ = "sterling.peet@gatech.edu"
__date__ = "2015-07-13"
__version__ = "1.0"

HOST =  "192.168.10.114"
HOST0 = "0.0.0.0"
PORT0 = 8106
PORT = 8105

ctlReg = 0x2f # 0x2f for Eval Board
ctlMode = 0x01

delayTime = 0.1

if __name__=='__main__':
  #ctl = FPGAcmd(HOST, PORT, HOST0, PORT0, 1, 102400)
  avr = AVRcmd(HOST, PORT, HOST0, PORT0)
  ctl = avr.getFPGA()

  print 'Test: uC Power On Self Test'
  print 'Purpose: Read out uC Self Test information to verify basic hardware connections.'
  print 'uC Firmware: PeltierPOST_v5.hex'
  print ''

  speed = 0x20  # This has a low probability of transfer error by experiment

  # set up the uC
  cmdOutput = ctl.sendCmd(ctlReg, 1, 0x2000, 0)
  print cmdOutput
  sleep(delayTime)

  # Set up the uC SPI speed
  cmdOutput = ctl.sendCmd(ctlReg, 1, (speed << 8 | ctlMode), 0)
  print cmdOutput
  sleep(delayTime)

  thisLine = ""
  errCount = 0 # This counts non-printable chars that are not 6 (ACK)

  for i in range(10):

    results = [0,0,0,0] #,0,0,0,0,0,0,0,0]
    # Reset uC buffer pointer
    avr.cmd(0xff)
    # Get 1st block of data (0x16 is SYN Idle)
    data = avr.cmd(0x0)
    results[0] = (data & 0xFF000000) >> 24
    results[1] = (data & 0x00FF0000) >> 16
    results[2] = (data & 0x0000FF00) >> 8
    results[3] = data & 0xFF

    print 'Speed:', hex(speed), 'String Retrieved:', "".join(map(chr,results)), 'Bytes:', results

    byte = results[0]

    if byte >= 32 and byte <= 126:
      thisLine = thisLine + chr(byte)
    elif byte == 0xd:
      print "AVR:", thisLine
      thisLine = ""
  print thisLine


