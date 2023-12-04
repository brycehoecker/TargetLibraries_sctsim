#!/usr/bin/python
import FPGAcmd
from time import sleep
from time import time

__author__ = "Sterling Peet"
__author_email__ = "sterling.peet@gatech.edu"
__date__ = "2014-10-08"
__version__ = "1.2"

# set some constants
wordSize = 2;  # 16 bit (2 byte) words
pageSize = 64; # 64 words in page

# It is possible to request the response of the 32-bit transaction before
# the FPGA has time to complete the SPI transaction.  When this happens,
# the FPGA returns whatever bits have been shited into register 0x31. My
# tests indicate the response bits are stable with a minimum sleep time
# of 0.0005 seconds, so double it to be sure this works all the time and
# on all systems.
# NOTE: This is dependant on the timing setting of the FPGA SPI bus in
#       Register 0x2f, and should be adjusted accordingly.
minRequestResponseTime = 0.001

t_startup = 0.03;  # min 20 milliseconds
twd_flash = 0.005; # 5 milliseconds
twd_eeprom = 0.004;
twd_erase = .01;

# uCctl = '0x2f'; # Peltier uC control register address
# uCdato = '0x30'; # Data to uC register address
# uCdati = '0x31'; # Data from uC register address
uCctl = '0x21'; # Peltier uC control register address
uCdato = '0x22'; # Data to uC register address
uCdati = '0x23'; # Data from uC register address

nullByte = '0x00'

Read_Signature_Byte = '0x30'

HOST =  "192.168.0.173"
HOST0 = "0.0.0.0" # Apparently this works for linux, but 127.0.0.1 is necessary for mac?
PORT0 = 8106
PORT = 8105
FUSE_TIMEOUT = 6 # seconds
RDY_BUSY_TIMEOUT = t_startup #seconds

class SafeByteError(Exception):
  '''Exception raised when the safety mechanism is not disabled before
  attempting to execute a potentially dangerous programming mode AVR
  instruction.

  Attributes:
     cmd  -- input instruction causing the error
     msg  -- explanation of the error
  '''

  def __init__(self, cmd, msg):
    self.cmd = cmd
    self.msg = msg

  def __str__(self):
    return repr(self.msg + ": " + hex(self.cmd))

class OutOfBoundsError(Exception):
  '''Exception raised when the value being used is outside acceptable
  bounds for the context.

  Attributes:
     val  -- input value causing the error
     msg  -- explanation of the error
  '''

  def __init__(self, val, msg):
    self.val = val
    self.msg = msg

  def __str__(self):
    return repr(self.msg + ": " + hex(self.cmd))

class TimeoutError(Exception):
  '''Exception raised when a timeout expires.

  Attributes:
     val -- timeout length that has expired
     msg -- explanation of the timeout
  '''

  def __init__(self, val, msg):
    self.val = val
    self.msg = msg

  def __str__(self):
    return repr(self.msg + ": " + hex(self.cmd))

class AVRcmd(object):
  '''This class abstracts the raw FPGA communication protocol 
  to a managable command and response API for programming an AVR
  device.'''

  def __init__(self, targetIP, targetPort, localHost, localPort):
    self.__targetIP = targetIP
    self.__targetPort = targetPort
    self.__localHost = localHost
    self.__localPort = localPort
    self.__fpga = FPGAcmd.FPGAcmd(targetIP, targetPort, localHost, localPort, 1, 102400)
    self.__sendReadCmd = 0
    self.__sendWriteCmd = 1
    self.__sendNoResponse = 0
    self.__safeMode = True
    self.__safeByte = eval('0xAC')
    self.dryRun = False
    self.printPacketInfo = 0
    self.__RDY = 0x00
    self.__BSY = 0x01
    self.readyBusyTimeout = .1
    self.__chipEraseByte = '0x80'
    self.lastResponseWord = 0xFFFFFFFF
    self.lastResponseByte = 0xFF
    self.setupSleep = 0.005
    self.__setupPgm1 = 0x2002
    self.__setupPgm2 = 0x2003
    self.__validPgmCtlResp = 0x80002003
    self.__removeReset = 0x2007
    self.__normalSPI = 0x2001
    self.pgmFlashLow = 0x40
    self.pgmFlashHigh = 0x48
    self.__pgmAddressMask = 0x3F
    self.pgmFlashPage = 0x4C
    self.readFlashLow = 0x20
    self.readFlashHigh = 0x28

  def getFPGA(self):
    '''For use when the default AVRcmd configuration of FPGAcmd
    is insufficient.'''
    return self.__fpga

  def unSafe(self):
    '''Unset the safety flag so we can perform a potentially dangerous
    operation.'''
    self.__safeMode = False

  def packBytes(self, byte1, byte2, byte3, byte4):
    '''Pack 4 bytes, chars or hex, into 1 bigger 32-bit integer.'''
    _byte1 = eval(byte1)
    _byte2 = eval(byte2)
    _byte3 = eval(byte3)
    _byte4 = eval(byte4)
    cmdVal = (_byte1<<24 | _byte2<<16 | _byte3 <<8 | _byte4)
    return cmdVal

  def unpackBytes(self, cmdVal):
    '''Unpack a 32-bit integer into 4 bytes, put them into a dictionary.'''
    _byte1 = (cmdVal & 0xFF000000) >> 24
    _byte2 = (cmdVal & 0x00FF0000) >> 16
    _byte3 = (cmdVal & 0x0000FF00) >> 8
    _byte4 = (cmdVal & 0x000000FF)
    return {"byte1": _byte1, "byte2": _byte2,
            "byte3": _byte3, "byte4": _byte4}

  def unpackHexBytes(self, cmdVal):
    '''Unpack a 32-bit integer into 4 bytes, put them into a dictionary
    as text strings containing hex values.'''
    byteDict = unpackBytes(cmdVal)
    return {"byte1": hex(byteDict.get("byte1")),
            "byte2": hex(byteDict.get("byte2")),
            "byte3": hex(byteDict.get("byte3")),
            "byte4": hex(byteDict.get("byte4"))}

  def __checkForSafeByte(self, cmdVal, message='None'):
    '''This helper checks to make sure we un-set safe mode before attempting
    to run a protected programming instruction.  Raises a SafeByteError
    exception if still in safe mode, and puts us back in safe mode if not.'''
    checkByte = (cmdVal & 0xFF000000) >> 24
    if checkByte == self.__safeByte:
      if self.__safeMode:
        if message == 'None':
          message = 'Failed Safety Check against ' + hex(self.__safeByte)
        raise SafeByteError(cmdVal, message)
      else:
        self.__safeMode = True

  def cmd(self, cmdVal):
    '''Computation friently method, using a 32-bit integer input to generate
    a 32-bit value response.'''
    result = self.__cmd(cmdVal)
    return eval(result.get("Data"))

  def byteCmd(self, byte1, byte2, byte3, byte4):
    '''This method is the raw glory of communicating with the FPGA,
    it handles the nasty interface and makes it manageable and
    relevant to the AVR programming task.'''
    cmdVal = self.packBytes(byte1, byte2, byte3, byte4)
    result = self.__cmd(cmdVal)
    response = eval(result.get("Data"))
    return self.unpackBytes(response)

  def byteHexCmd(self, byte1, byte2, byte3, byte4):
    '''This method communicates with the FPGA, handles the nasty interface,
    and makes it manageable and relevant to the AVR programming task.
    Returns dictionary of bytes with hex string values.'''
    cmdVal = self.packBytes(byte1, byte2, byte3, byte4)
    result = self.__cmd(cmdVal)
    response = eval(result.get("Data"))
    return self.unpackHexBytes(response)

  def __printPacketInfo(self, response, titleStr):
    '''This handles printing out debug info for a response based on the
    verbosity indicated in AVRcmd.printPacketInfo'''
    if self.printPacketInfo > 0:
      print "\n" + titleStr
    if self.printPacketInfo > 1:
      print "Serial Number:", response.get("SerNum")
    if (self.printPacketInfo > 2) or (response.get("Errors") != "0x0"):
      print "Errors: ", response.get("Errors")
    if self.printPacketInfo > 0:
      print "Register:", response.get("Addr")
    if self.printPacketInfo > 0:
      print "Data:", response.get("Data")
    if self.printPacketInfo > 2:
      print "Tail:", response.get("Tail")
      print "Protocol:", response.get("Protocol")

  def __cmd(self, cmdVal):
    '''Workhorse method to communicate with the FPGA under the hood.'''
    self.__checkForSafeByte(cmdVal)
    if self.dryRun:
      result = {"Data": hex(cmdVal >> 8)}
    else:
      result = self.__fpga.sendCmd(eval(uCdato), self.__sendWriteCmd,
                                   cmdVal, self.__sendNoResponse)
      # Here we should check that we got a good response
      sleep(minRequestResponseTime)
      self.__printPacketInfo(result, "AVR Instruction Packet")
      result = self.__fpga.sendCmd(eval(uCdati), self.__sendReadCmd,
                                   self.__sendReadCmd, self.__sendNoResponse)
      # TODO: A good response is 1 byte behind the sent byte, but sometimes
      #       byte4 is a response byte for the instruction.
      self.__printPacketInfo(result, "AVR Response Packet")
      self.lastResponseWord = eval(result.get("Data"))
      self.lastResponseByte = self.unpackBytes(self.lastResponseWord).get('byte4')
    return result

  def __pollReadyBusy(self):
    '''Ask the uC if it is Busy or not (Workhorse).'''
    response = self.responseByte('0xF0', nullByte, nullByte, nullByte)
    return response & 0x01

  def waitUntilReady(self):
    '''Poll the uC for its RDY/BSY status, and wait until the uC is ready
    to continue (or timeout)'''
    continueWaitingFlag = True
    startTime = time()
    timeIsUp = time() + self.readyBusyTimeout
    restorePacketInfo = self.printPacketInfo
    cycles = 0
    if self.printPacketInfo > 0:
      self.printPacketInfo = restorePacketInfo - 1
    while continueWaitingFlag:
      cycles = cycles + 1
      if self.__pollReadyBusy() == self.__RDY:
        continueWaitingFlag = False
      else:
        if time() > timeIsUp:
          raise TimeoutError(self.readyBusyTimeout,
            'AVR is not yet ready, timeout')
    if restorePacketInfo > 0:
      print 'Waited', time() - startTime, 'seconds,', cycles, ('cycle(s) ' +
        'for RDY status')
    self.printPacketInfo = restorePacketInfo

  def chipErase(self):
    '''Erase the chip's memory with the chip erase instruction.'''
    self.unSafe()
    self.byteCmd(hex(self.__safeByte), self.__chipEraseByte, nullByte, nullByte)
    self.waitUntilReady()

#  def sendCmd(self, byte1, byte2, byte3, byte4):
#    '''This command type is for sending commands to an AVR that do 
#    not expect a response from the device other than the echo
#    characters.'''
#    _byte1 = eval(byte1)
#    _byte2 = eval(byte2)
#    _byte3 = eval(byte3)
#    _byte4 = eval(byte4)
#    res = self.cmd(_byte1, _byte2, _byte3, _byte4)
 #   if ((_byte1 != res.get("byte2") or (_byte2 != res.get("byte3")) or (_byte3 != res.get("byte4"))):
#      print "One of the bytes does not match!"
#    return response

  def __respByte(self, byte1, byte2, byte3, byte4):
    '''Workhorse command returns a response byte.'''
    result = self.cmd(byte1, byte2, byte3, byte4)
    return eval(result.get('byte4'))

  def responseByte(self, byte1, byte2, byte3, byte4):
    '''This command type returns a response byte.'''
    result = self.byteCmd(byte1, byte2, byte3, byte4)
    return result.get('byte4')

  def writeFuse(self, byte1, byte2, fuseVal, timeout):
    '''Write fuse values to the fuse registers of the device.'''
    fuseVal = hex(eval(fuseVal) & 0x000000FF) # Truncate, user can abort later
    print '** Running Unsafe Command!'
    self.unSafe()
    print "** Preparing to write fuse value:", fuseVal
    print "** (CTRL-C) to abort"
    sleep(timeout)
    self.cmd(self.packBytes(byte1, byte2, nullByte, fuseVal))
    self.waitUntilReady()

  def startPgmMode(self):
    '''Check if we are in programming mode, attempt to start the programming
    mode if we are in normal mode.'''
    if not self.dryRun:
      # First Check if we are not already in Programming Mode
      resp = self.__fpga.sendCmd(eval(uCctl), self.__sendReadCmd,
                          self.__sendReadCmd, self.__sendNoResponse)
      if eval(resp.get("Data")) != self.__validPgmCtlResp:
        # Try putting the FPGA in uC programming Mode
        if self.printPacketInfo > 0:
          print '*** Sending packets to Put FPGA in uC Programming Mode'
        self.__fpga.sendCmd(eval(uCctl), self.__sendWriteCmd,
                            self.__setupPgm1, self.__sendNoResponse)
        sleep(self.setupSleep) # Let the setting stick

        self.__fpga.sendCmd(eval(uCctl), self.__sendWriteCmd,
                            self.__setupPgm2, self.__sendNoResponse)
        sleep(0.1)#sleep(t_startup) # Give everything a chance to set up
        resp = self.__fpga.sendCmd(eval(uCctl), self.__sendReadCmd,
                            self.__sendReadCmd, self.__sendNoResponse)

        if eval(resp.get("Data")) == self.__validPgmCtlResp:
          if self.printPacketInfo > 0:
            print '*** FPGA entered command mode:', resp.get('Data')
          # Double check we also got a good response from the uC
          uCresp = self.__fpga.sendCmd(eval(uCdati), self.__sendReadCmd,
                            self.__sendReadCmd, self.__sendNoResponse)
          if eval(uCresp.get("Data")) != 0x5300:
            print '*** AVR did NOT respond Correctly for Programming Mode!', uCresp.get('Data')
          else:
            if self.printPacketInfo > 0:
              print '*** AVR responded with Programming Mode Enabled:', uCresp.get('Data')
        else:
          print '*** FPGA did not go into uC Programming Mode!'
      else:
        if self.printPacketInfo > 0:
          print '*** FPGA was already in Programming Mode.'

  def removeReset(self):
    '''Send a control command to remove the reset signal and exit command
    mode.'''
    if not self.dryRun:
      self.__fpga.sendCmd(eval(uCctl), self.__sendWriteCmd,
                          self.__removeReset, self.__sendNoResponse)
      self.__fpga.sendCmd(eval(uCctl), self.__sendWriteCmd,
                          self.__normalSPI, self.__sendNoResponse)

  def loadFlashWord(self, address, word):
    '''Load a full 16-bit word into the full address specified.  This
    method will handle appropriate address mangling and byte loading
    order.  The address and word should not be strings.'''
    # Within the same page, the low data byte must be loaded prior to the high
    # data byte.
    address = address & self.__pgmAddressMask
    lowWord = hex(word & 0xFF)
    highWord = hex((word & 0xFF00) >> 8)
    self.__cmd(self.packBytes(hex(self.pgmFlashLow),nullByte,hex(address),lowWord))
    self.__cmd(self.packBytes(hex(self.pgmFlashHigh),nullByte,hex(address),highWord))

  def readFlashWord(self, address):
    '''Read a full 16-bit word from the flash memory address specified.'''
    addressMSB = (address & 0xFF00) >> 8
    addressLSB = (address & 0xFF)
    self.__cmd(self.packBytes(hex(self.readFlashLow),hex(addressMSB),
               hex(addressLSB),nullByte))
    lowWord = self.lastResponseByte
    self.__cmd(self.packBytes(hex(self.readFlashHigh),hex(addressMSB),
               hex(addressLSB),nullByte))
    highWord = self.lastResponseByte
    return (highWord << 8) | lowWord

  def verifyFlashWord(self, address, word):
    '''Compare the word to the word stored in the address of the uC's flash
    memory.  Returns True if they match, and False if they do not.'''
    testWord = self.readFlashWord(address)
    if testWord == word:
      return True
    else:
      return False

  def writeFlashPage(self, address):
    '''Writes the whole contents of the page buffer into the page that
    contains the memory address given as the argument.'''
    addressMSB = (address & 0xFF00) >> 8
    addressLSB = (address & ~self.__pgmAddressMask)
    self.__cmd(self.packBytes(hex(self.pgmFlashPage), hex(addressMSB),
       hex(addressLSB), nullByte))
    self.waitUntilReady()

if __name__ == "__main__":
  import argparse
  import textwrap

  parser = argparse.ArgumentParser(
    description=textwrap.dedent('''\
    Use this program to send individual commands to the AVR in programming mode.
    Refer to page 301 of the Atmel ATmega328 datasheet.'''),
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog = textwrap.dedent('''\
    Written by Sterling Peet <sterling.peet@gatech.edu>, under
    Nepomuk Otte <http://otte.gatech.edu>
    Center for Relativistic Astrophysics
    Georgia Institute of Technology
    Atlanta, GA, USA'''))
    # version='%(prog)s {version}, ({date})'.format(version=__version__,
    # date=__date__))
  parser.add_argument('byte1', default=Read_Signature_Byte, nargs='?',
    help='Byte 1 of AVR Programming Instruction')
  parser.add_argument('byte2', default=nullByte, nargs='?',
    help='Byte 2 of AVR Programming Instruction')
  parser.add_argument('byte3', default=nullByte, nargs='?',
    help='Byte 3 of AVR Programming Instruction')
  parser.add_argument('byte4', default=nullByte, nargs='?',
    help='Byte 4 of AVR Programming Instruction')
  parser.add_argument('-V', '--version', action='version',
    version='%(prog)s {version}, ({date})'.format(version=__version__,
    date=__date__))
  parser.add_argument('-e', '--erase', action='store_true',
    help='Erase the chip\'s memory before running instruction')
  parser.add_argument('-d', '--dry_run', action='store_true',
    help='Display hex commands instead of running them')
  parser.add_argument('-u', '--unsafe', action='store_true',
    help='Disable safety check for using unsafe AVR instructions')
  parser.add_argument('-v', '--verbose', action='count',
    help='Increase output verbosity')
  parser.add_argument('--target_host', default=HOST,
    help='IP address of the TARGET fpga')
  parser.add_argument("--target_port", default=PORT, type=int,
    help='Port the TARGET fpga is listening on')
  parser.add_argument('--rx_port', default=PORT0, type=int,
    help='Local port to listen on for TARGET response packets')
  parser.add_argument('--fuse_timeout', default=FUSE_TIMEOUT, type=int,
    help='How long the user has to recognize a fuse error and abort writing')
  parser.add_argument('--r_lfuse', action='store_true', help='Read Low Fuses')
  parser.add_argument('--r_hfuse', action='store_true', help='Read High Fuses')
  parser.add_argument('--r_efuse', action='store_true',
    help='Read Extended Fuses')
  parser.add_argument('--w_lfuse', default='None', help='Write Low Fuses')
  parser.add_argument('--w_hfuse', default='None', help='Write High Fuses')
  parser.add_argument('--w_efuse', default='None', help='Write Extended Fuses')
  parser.add_argument('--rdy_bsy_timeout', default=RDY_BUSY_TIMEOUT, type=int,
    help='Length of time to wait for uC while it indicates it is busy')
  parser.add_argument('--load_pgm_word', action='store_true',
    help='Load a 16-bit word into the flash program memory using a full length \
    address specified in the byte1 argument and 16-bit word specified in the \
    byte2 argument.')
  parser.add_argument('--read_pgm_word', action='store_true',
    help='Read a 16-bit word out of the flash program memory from the address \
    specified in the byte1 argument')
  parser.add_argument('--verify_pgm_word', action='store_true',
    help='Check the word in the flash memory at the address specified in the \
    byte1 argument and find out if it matches the word specified in the byte2 \
    argument.')
  parser.add_argument('--write_pgm_page', action='store_true',
    help='Write the contents of the program memory page buffer to the page \
    that begins at the address specified in the byte1 argument')
  parser.add_argument('-s', '--start_pgm_mode', action='store_true',
    help='Ensure programming mode is active before attempting to run command')
  parser.add_argument('--end_pgm_mode', action='store_true',
    help='Exit programming mode and remove the reset signal from the AVR')

  args = parser.parse_args()

  avr = AVRcmd(args.target_host, args.target_port, HOST0, args.rx_port)
  if args.dry_run:
    avr.dryRun = True
  avr.printPacketInfo = args.verbose
  avr.readyBusyTimeout = args.rdy_bsy_timeout

  # Start programming mode if requested
  if args.start_pgm_mode:
    print '** Starting AVR Programming Mode'
    avr.startPgmMode()

  # TODO: Investigate the Device Signature

  # Investigate the Fuses
  if args.r_lfuse or (args.w_lfuse != 'None'):
    print 'Reading Low Fuse Byte:'
    lowByte = avr.responseByte('0x50', nullByte, nullByte, nullByte)
    print 'Low Fuse Byte:', hex(lowByte)

  if args.w_lfuse != 'None':
    print 'Writing Low Fuse Byte:', args.w_lfuse
    avr.writeFuse('0xAC', '0xA0', args.w_lfuse, args.fuse_timeout)
    print 'Reading Low Fuse Byte:'
    lowByte = avr.responseByte('0x50', nullByte, nullByte, nullByte)
    print 'Low Fuse Byte:', hex(lowByte)

  if args.r_hfuse or (args.w_hfuse != 'None'):
    print 'Reading High Fuse Byte:'
    highByte = avr.responseByte('0x58', '0x08', nullByte, nullByte)
    print 'High Fuse Byte:', hex(highByte)

  if args.w_hfuse != 'None':
    print 'Writing High Fuse Byte:', args.w_hfuse
    avr.writeFuse('0xAC', '0xA8', args.w_hfuse, args.fuse_timeout)
    print 'Reading High Fuse Byte:'
    highByte = avr.responseByte('0x58', '0x08', nullByte, nullByte)
    print 'High Fuse Byte:', hex(highByte)

  if args.r_efuse or (args.w_efuse != 'None'):
    print 'Reading Extended Fuse Byte:'
    extendedByte = avr.responseByte('0x50', '0x08', nullByte, nullByte)
    print 'Extended Fuse Byte:', hex(extendedByte)

  if args.w_efuse != 'None':
    print 'Writing Extended Fuse Byte:', args.w_efuse
    avr.writeFuse('0xAC', '0xA4', args.w_efuse, args.fuse_timeout)
    print 'Reading Extended Fuse Byte:'
    extendedByte = avr.responseByte('0x50', '0x08', nullByte, nullByte)
    print 'Extended Fuse Byte:', hex(extendedByte)

  # Erase Chip's Memory
  if args.erase:
    print '** Running Unsafe Command!'
    print '** Erasing Memory...'
    avr.chipErase()
    print '** Done.'

  if args.verify_pgm_word:
    print 'Verifying word', args.byte2, 'in address', args.byte1
    result = avr.verifyFlashWord(eval(args.byte1), eval(args.byte2))
    if result:
      print 'Successfully Verified.'
    else:
      print 'Word does not match', hex(avr.readFlashWord(eval(args.byte1)))
  elif args.read_pgm_word:
    print 'Reading word in address', args.byte1
    word = avr.readFlashWord(eval(args.byte1))
    print 'Word:', hex(word)
  elif args.load_pgm_word:
    print 'Loading word', args.byte2, 'into address', args.byte1, '(', \
      hex(eval(args.byte1) & 0x3F), ')'
    avr.loadFlashWord(eval(args.byte1), eval(args.byte2))
  elif args.write_pgm_page:
    print 'Writing page buffer to page', hex(eval(args.byte1) & (~0x003F)), \
          'containing address', args.byte1
    avr.writeFlashPage(eval(args.byte1))
  else:
    # Run user's command!
    command = avr.packBytes(args.byte1, args.byte2, args.byte3, args.byte4)
    print "* cmd     :", hex(command)
    if args.unsafe:
      print '** Running Unsafe Command!'
      avr.unSafe()
    result = avr.cmd(command)
    if args.verbose > 0:
      print "* out word:", hex(result)
    print "* out byte: ", hex(avr.lastResponseByte)

  # If the user wanted to load or write something, we should make sure
  # the microcontroller is ready before we exit, otherwise a new call to
  # the same program could happen fast enough to corrupt data in the
  # microcontroller.
  if ((args.unsafe == True) or (eval(args.byte1) == 0x40) or
     (eval(args.byte1) == 0x48) or (eval(args.byte1) == 0x4C) or
     (eval(args.byte1) == 0x4D) or (eval(args.byte1) == 0xC0) or
     (eval(args.byte1) == 0xC1) or (eval(args.byte1) == 0xC2) or
     (eval(args.byte1) == 0xAC)):
    avr.waitUntilReady()

  if args.end_pgm_mode:
    print "** Exiting Programming Mode and removing reset signal!"
    avr.removeReset()
