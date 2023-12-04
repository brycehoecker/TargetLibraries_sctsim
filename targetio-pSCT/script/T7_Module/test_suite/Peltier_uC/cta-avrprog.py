#!/usr/bin/env python
from __future__ import division
from math import ceil
import os
from progressbar import *
import intelhex
import AVRcmd
from time import sleep
from time import time
from string import split

__author__ = "Sterling Peet"
__author_email__ = "sterling.peet@gatech.edu"
__date__ = "2014-10-09"
__version__ = "1.1"

HOST =  "192.168.0.173"
HOST0 = "0.0.0.0" # Apparently this works for linux, but 127.0.0.1 is necessary for mac?
PORT0 = 8106
PORT = 8105

class FileTransferSpeed1024(FileTransferSpeed):
    '''Widget for showing the transfer speed (useful for file transfers) but
    uses the 8-bit (1024) scale units instead of 1000 scale.'''
    def update(self, pbar):
        if pbar.seconds_elapsed < 2e-6:#== 0:
            bps = 0.0
        else:
            bps = float(pbar.currval) / pbar.seconds_elapsed
        spd = bps
        for u in self.units:
            if spd < 1024:
                break
            spd /= 1024
        return self.fmt % (spd, u+'/s')

# http://stackoverflow.com/questions/5166473/inheritance-and-init-method-in-python
class TimeProgressBar(ProgressBar):
  def __init__(self, maxval=100, widgets=default_widgets, term_width=None,
               fd=sys.stderr):
    ProgressBar.__init__(self, maxval, widgets, term_width, fd)
    self.updateInterval = 0.125 # Seconds, can be modified
    self.__lastUpdate = time()

  def _need_update(self):
    timeNow = time()
    percent = self.percentage()
    if (percent == 0) or (percent == 100):
      return True
    elif (timeNow - self.__lastUpdate) >= self.updateInterval:
      self.__lastUpdate = timeNow
      return True
    else:
      return False

class AtmelProgrammer(object):
  '''This class is useful for performing firmware loading and verification
  procedures for AVR microcontrollers. The variable avrcmd contains the
  object for running programming instructions on the AVR. The variable
  binArray contains the array of 16-bit binary words to be programmed into
  the AVR.'''
  def __init__(self, avrcmd, binArray=None, progressbar=None):
    self.avr = avrcmd
    self.binArray = binArray
    self.pbar = progressbar
    self.__pbarId = None
    self.wordSize = 2;  #% 16 bit (2 byte) words
    self.pageSize = 64; #% 64 words in page

  def _pbarStart(self, identStr, maxval=100):
    '''This is supposed to set up and start the progress bar.  The identStr
    argument is a string identifying the purpose of the bar.  This string
    should be unique for different operations, for display purposes and
    performance caching purposes.'''
    self.__pbarId = identStr
    if self.pbar != None:
      self.pbar.maxval = maxval
      print identStr + ': '
      # print 'starting pbar', identStr, '\n'
      if self.pbar.finished:
        self.pbar.finished = False
        self.pbar.start_time = None
        self.pbar.seconds_elapsed = 0
      self.pbar.start()

  def _pbarUpdate(self, value):
    '''This should be called for every work unit performed.  The value is
    the current work unit\'s value with respect to the maxval.  A higher
    value than maxval will set maxval to the current value.'''
    if self.pbar != None:
      if value > self.pbar.maxval:
        self.pbar.maxval = value
      self.pbar.update(value)

  def _pbarFinish(self):
    '''This is called after the last progress update and the multi-part
    operation is complete.'''
    if self.pbar != None:
      self.pbar.finish()

  def chipErase(self):
    '''Erase the program memory of the AVR.'''
    self.avr.startPgmMode()
    self.avr.chipErase()

  def _checkBinArray(self, binArray):
    if (binArray == None):
      if (self.binArray == None):
        print '*** No firmware to compare with AVR memory!'
        raise Error
    else:
      self.binArray = binArray

  def loadFirmware(self, binArray=None):
    '''Load the firmware into the AVR program memory.'''
    self._checkBinArray(binArray)

    self.avr.startPgmMode()
    self.chipErase()
    wordTotal = len(self.binArray)
    self._pbarStart('Loading Firmware', 2*wordTotal)
    thisPage = 0;
    pageTotal = int(ceil(wordTotal / self.pageSize))
    # print 'Loading', pageTotal, 'pages into uC'

    # Loop through each page, load the words, then write the page
    #   to memory.
    for pageIndex in range(pageTotal):
      pageAddr = pageIndex * self.pageSize
      endAddr = min(pageAddr+self.pageSize, wordTotal)
      # Loop through every word in the page, load it into the page cache
      for wordAddr in range(pageAddr, endAddr):
        self.avr.loadFlashWord(wordAddr, self.binArray[wordAddr])
        self._pbarUpdate(2*wordAddr)
      self.avr.writeFlashPage(pageAddr)
    self._pbarFinish()
    print 'Fimware Loading Complete.'

  def verifyFirmware(self, binArray=None):
    self._checkBinArray(binArray)

    self._pbarStart('Verify Firmware Load', 2*len(self.binArray))
    self.avr.startPgmMode()
    verifyPass = True
    for index in range(len(self.binArray)):
      if not (avr.verifyFlashWord(index,self.binArray[index])):
        print 'Word', hex(self.binArray[index]), 'does not match uC at address', \
              hex(index), ':', hex(avr.readFlashWord(index)), '   ###'
        verifyPass = False
      self._pbarUpdate(2*index)
    self._pbarFinish()
    return verifyPass

if __name__=='__main__':
  import argparse
  import textwrap

  parser = argparse.ArgumentParser(description=textwrap.dedent('''\
    UDP based FPGA programmer mechanism for loading application code into the 
    module\'s ATmega temperature controller uC.

    Example Invocation:\n

    %(prog)s -p m328 -U flash:w:blink.hex
    '''),
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog = textwrap.dedent('''\
    This program is intended to run in place of the open source firmware loading
    tool /'avrdude/'.

    Written by Sterling Peet <sterling.peet@gatech.edu>, under
    Nepomuk Otte <http://otte.gatech.edu>
    Center for Relativistic Astrophysics
    Georgia Institute of Technology
    Atlanta, GA, USA''') )
  parser.add_argument('--version', action='version',
    version='%(prog)s {version}, ({date})'.format(version=__version__,
    date=__date__))
  # parser.add_argument('hex_file', help='Intel Hex file to load into the uC.')
  parser.add_argument('--target_host', default=HOST,
    help='IP address of the TARGET fpga')
  parser.add_argument("--target_port", default=PORT, type=int,
    help='Port the TARGET fpga is listening on')
  parser.add_argument('--rx_port', default=PORT0, type=int,
    help='Local port to listen on for TARGET response packets')
  parser.add_argument('-U', '--upload', 
    help='<memtype>:r|w|v:<filename>[:format] Memory operation specification. \
      Only write/verify flash is currently supported.')
  parser.add_argument('-p', '--partno', help='Required. Specify AVR device.')
  parser.add_argument('-n', '--no_write', action='store_true',
    help='Do not write anything to the device.')
  parser.add_argument('-V', '--no_verify', action='store_true',
    help='Do not verify.')
  group = parser.add_mutually_exclusive_group()
  group.add_argument("-v", "--verbosity", action="count", default=0,
    help='Verbose output. -v -v for more.')
  group.add_argument("-q", "--quiet", action="count", default=0,
    help='Quell progress output. -q -q for less.')
  parser.add_argument('-C')
  parser.add_argument('-c')

  args = parser.parse_args()
  # print(args.accumulate(args.integers))

  memUpload = split(args.upload, ':')

  avr = AVRcmd.AVRcmd(args.target_host, args.target_port, HOST0, args.rx_port)
  if args.no_write:
    avr.dryRun = True

  if len(memUpload) > 2:
    if memUpload[0] == 'flash':
      hexFile = intelhex.IntelHex16bit(memUpload[2])
      firmware = hexFile.tobinarray()

      widgets = ['Progress: ', Percentage(), ' ', Bar(left='[',right=']'),
         ' ', ETA(), ' ', FileTransferSpeed1024()]
      progress = TimeProgressBar(widgets=widgets)
      if args.quiet > 0:
        progress = None

      avrLoader = AtmelProgrammer(avr, firmware, progress)

      if memUpload[1] == 'w':
        avrLoader.loadFirmware()
        if not args.no_verify:
          verifyPass = avrLoader.verifyFirmware()
      elif memUpload[1] == 'v':
        verifyPass = avrLoader.verifyFirmware()

      if verifyPass:
        print 'Successfully Verified Memory'
      else:
        print '*** Memory does not match original firmware file!'
        raise Exception('Memory does not match original firmware file')

  avr.removeReset()
  print
