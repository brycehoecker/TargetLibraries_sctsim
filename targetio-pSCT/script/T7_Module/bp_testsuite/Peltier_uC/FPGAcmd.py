#!/usr/bin/env python
from socket import *
import string
from datetime import datetime
from time import sleep

__author__ = "Sterling Peet"
__author_email__ = "sterling.peet@gatech.edu"
__date__ = "2014-11-14"
__version__ = "1.2"

TIMEOUT = '1'
READ = 0
DATA_0 = '0'
REG_0 = DATA_0
RSP_NONE = '0'
HOST =  "192.168.0.173"
HOST0 = "0.0.0.0" # Apparently this works for linux, but 127.0.0.1 is necessary for mac?
PORT0 = 8106
PORT = 8105
buffer = 102400

class PeltierController(object):
  '''This object is used for controlling the state of the Peltier uC via 
     the control register(s) in the FPGA.'''
  def __init__(self, fpga):
    self.__fpga = fpga
    self.__default_speed = 0x20
    self.__speed = 0
    self.__eval_register = 0x2f
    self.__production_register = 0x21
    self.__config_register = 0
    self.__spi_read_reg = 0
    self.__spi_write_reg = 0
    self.__spi_transfer_time = 0
    self.printPacketInfo = 0
    self.setupSleep = 0.005
    self.uCStartupTime = 0.2
    self.__setupPgm1 = 0x02
    self.__setupPgm2 = 0x03
    self.__removeReset = 0x07
    self.__normalSPI = 0x01
    self.__pgmModeSuccess = 0x5300
    self.setProductionEnv()
    self.setSpeed(self.__default_speed)

  def __config(self, mode):
    '''Returns the config register word for the desired mode byte.'''
    _mode = mode & 0x07
    return _mode + (self.__speed << 8)

  def setEvalEnv(self):
    '''Set the register numbers for communicating with the eval board.'''
    self.__config_register = self.__eval_register
    self.__spi_write_reg = self.__config_register + 1
    self.__spi_read_reg = self.__spi_write_reg + 1

  def setProductionEnv(self):
    '''Set the register numbers for communicating with the production FPGA board.'''
    self.__config_register = self.__production_register
    self.__spi_write_reg = self.__config_register + 1
    self.__spi_read_reg = self.__spi_write_reg + 1

  def setSpeed(self, speed):
    '''Set the communication speed for the SPI bus.  Speed is 250 ns times the 
       speed argument, mod 256 (the lowest byte).'''
    self.__speed = speed & 0xFF
    self.__spi_transfer_time = 0.000000250 * 32 * self.__speed
    # Time buffer to make sure transfer completes properly before requesting
    #  the data back
    self.__spi_transfer_time = self.__spi_transfer_time * 4

  def transfer(self, word):
    '''Send a 32-bit word to the uC and get a 32-bit word back.'''
    self.__fpga.write(self.__spi_write_reg, word)
    sleep(self.__spi_transfer_time)
    return self.__fpga.read(self.__spi_read_reg)

  def __checkPgmStatus(self):
    '''Check and see if the status is complete, the speed matches our
       expectations, and we are in programming mode.'''
    config = self.__fpga.read(self.__config_register)
    speedOK = False
    complete = False
    modeOK = False
    if self.__speed == ((config & 0xFF00) >> 8 ):
      speedOK = True
    if (config >> 31) > 0:
      complete = True
    if self.__setupPgm2 == (config & 0xFF):
      modeOK = True
    return speedOK and complete and modeOK

  def programmingMode(self):
    '''Put the Peltier uC into programming mode, allowing the part to be
       reprogrammed.'''
    # First Check if we are not already in Programming Mode
    if not self.__checkPgmStatus():
      # Try putting the FPGA in uC programming Mode
      if self.printPacketInfo > 0:
        print '*** Sending packets to Put FPGA in uC Programming Mode'
      self.__fpga.write(self.__config_register, self.__config(self.__setupPgm1))

      sleep(self.setupSleep) # Let the setting stick

      self.__fpga.write(self.__config_register, self.__config(self.__setupPgm2))
      sleep(0.1)#sleep(t_startup) # Give everything a chance to set up

      if self.__checkPgmStatus():
        if self.printPacketInfo > 0:
          print '*** FPGA entered command mode:', hex(self.__fpga.lastData)
        # Double check we also got a good response from the uC
        resp = self.__fpga.read(self.__spi_read_reg)
        if resp != 0x5300:
          print '*** AVR did NOT respond Correctly for Programming Mode!', hex(resp)
          print '*** This usually happens if the wrong environment is used,'
          print '***   production on an EVAL board, or EVAl on a real Front End.'
        else:
          if self.printPacketInfo > 0:
            print '*** AVR responded with Programming Mode Enabled:', hex(resp)
      else:
        print '*** FPGA did not go into uC Programming Mode!'
    else:
      if self.printPacketInfo > 0:
        print '*** FPGA was already in Programming Mode.'

  def normalMode(self):
    '''Put the Peltier uC into normal SPI communication mode.'''
    config = self.__fpga.read(self.__config_register)
    mode = config & 0xFF
    speed = (config & 0xFF00) >> 8
    if self.printPacketInfo > 0:
      print '*** Setting Peltier uC to normal mode'
      print '*** Peltier Config Read:', hex(config)
      print '*** Extracted Mode:', hex(mode)
      print '*** Extracted Speed:', hex(speed)

    if (mode is not 0x01) or (speed is not self.__speed):
      if self.printPacketInfo > 0:
        print '*** Mode or speed mismatch:'
        print '*** Mode  (wanted):', hex(self.__speed)
        print '*** Speed (wanted):', hex(0x01)
      if mode > 0x01:
        if self.printPacketInfo > 0:
          print '*** Mode was greater than 0x01, resetting uC...'
        self.__fpga.write(self.__config_register, self.__config(0x07))
        sleep(self.setupSleep)
      self.__fpga.write(self.__config_register, self.__config(0))
      sleep(self.setupSleep)
      self.__fpga.write(self.__config_register, self.__config(1))
      sleep(self.setupSleep)
      if self.printPacketInfo > 1:
        config = self.__fpga.read(self.__config_register)
        print '*** Fresh uC config register:', hex(config)
      if mode > 0x01:
        sleep(self.uCStartupTime)

class SterlingCmdBuild(object):
    '''This class is based heavily upon LeonidCmdBuild, but with
       some minor fixes to make it function as part of an importable
       module.'''

    def __init__(self, address, readWrite, data, response):
      self.__address = address
      self.__readWrite = readWrite
      self.__data = data
      self.__response = response
      self.__cmd = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]    # 16 characters for 4 32 bit words

    def __setWrd0(self, data):
        return ((data & 0xFF000000) >>24 )

    def __setWrd1(self, data):
        return ((data & 0x00FF0000) >>16 )

    def __setWrd2(self, data):
        return ((data & 0x0000FF00) >>8 )

    def __setWrd3(self, data):
        return ((data & 0x000000FF) >>0 )

    def __setCmd(self, address, readWrite, data):
      cmdWord0 = 0x12345678
      cmdWord1 = ((readWrite & 1)<<30)+(address & 0x00ffffff)
      cmdWord2 = (data & 0xffffffff)
      cmdWord3 = 0xdeadbeef
      word0 = (self.__setWrd0(cmdWord0))
      word1 = (self.__setWrd1(cmdWord0))
      word2 = (self.__setWrd2(cmdWord0))
      word3 = (self.__setWrd3(cmdWord0))
      word4 = (self.__setWrd0(cmdWord1))
      word5 = (self.__setWrd1(cmdWord1))
      word6 = (self.__setWrd2(cmdWord1))
      word7 = (self.__setWrd3(cmdWord1))
      word8 = (self.__setWrd0(cmdWord2))
      word9 = (self.__setWrd1(cmdWord2))
      word10 = (self.__setWrd2(cmdWord2))
      word11 = (self.__setWrd3(cmdWord2))
      word12 = (self.__setWrd0(cmdWord3))
      word13 = (self.__setWrd1(cmdWord3))
      word14 = (self.__setWrd2(cmdWord3))
      word15 = (self.__setWrd3(cmdWord3))
      self.__cmd = [word0, word1, word2, word3, word4, word5, word6, word7, word8, word9, word10, word11, word12, word13, word14, word15]

    def getCmd(self):
        self.__setCmd(self.__address, self.__readWrite, self.__data)

        return self.__cmd

class FPGAcmd(object):
  '''The FPGAcmd class is designed to be a wrapper for the generic
  UDP interface used to communicate with the TARGET evaluation board.'''
  
  def __init__(self, targetIP, targetPort, localHost, localPort, 
               udpTimeout, receiveBufferLength):
    self.__printCmd = False
    self.__targetIP = targetIP
    self.__targetPort = targetPort
    self.__localHost = localHost
    self.__localPort = localPort
    self.__updTimeout = udpTimeout
    self.__receiveBuf = receiveBufferLength
    self.__UDPSock = socket(AF_INET,SOCK_DGRAM)
    self.__UDPSock.bind((self.__localHost,self.__localPort))
    self.__UDPSock.settimeout(self.__updTimeout)
    self.writeRegister = 1
    self.readRegister = 0
    self.responseTrue = 1
    self.responseFalse = 0
    self.show_time = False
    self.printPacketInfo = 0
    self.lastSerialNum = 0
    self.lastWrite = False
    self.lastAddress = 0
    self.lastData = 0
    self.lastErrors = 0
    self.lastTimeoutError = False
    self.lastOtherError = False
    self.lastTail = 0
    self.lastProtocol = 0

  def setPrintCmd(self, boolean):
    '''True prints the command packet byte array before sending the
    packet, False prevents printing to stdout.'''
    self.__printCmd = boolean

  def __waitForResponse(self):
    '''This is the response handling portion lifted directly from
    Leonid's PGPcmd_udp.py script.  I (Sterling) don't need this
    functionality, so programmatic access will require some refactoring
    to suit.'''
    print
    print
    still_data = 1
    k = 0
    n = 0
    b0 = 0
    b1 = 0

    if responseLength > 16:
      while (still_data):
        tmp = UDPSock.recvfrom(buffer)
        if len(tmp) == 2:
          data,addr = tmp
        else:
          print "timed out, bailing"
          break
#        for i in range(len(data)):
#          ptint 'Protocol data ', hex(ord(data[i]))
        k = k + 1
        n = n + 1
        if len(data) == 0:
          still_data = 0
        if (k > 0):
          #print 'Reply from: ', addr, data
          #LeonidRspPrint(responseLength, data)
          for i in range(len(data)):
#            if(b0 <= 1000):
            if ((i % 2) == 0):
              print 'Protocol data ', k,  i/2, hex((((ord(data[i+1])))) + ((ord(data[i]))<<8))
#            if(b1 <= 1):
#              print 'Protocol data ', k, hex(ord(data[i]))
#            if(i == 3):
#              if((ord(data[i]) & 0x3) == 1):
#                b0 = b0 + 1
#              if((ord(data[i]) & 0x3) == 2):
#                b1 = b1 + 1
#                print 'Protocol data ', k, hex(ord(data[i]))
#           if (n%64) == 0:
          #if (n>1500):
#           print 'Count ', n, b0, b1

  def sendCmd(self, register, readWrite, data, response):
    '''Send a command to the TARGET, which should repond to the command.
    The contents of the response are extracted from the message, then loaded
    into a dictionary as text string keys and text string hex values.'''

    nullResponse = '0';
    SerNum = nullResponse  # TODO: Use this to check for missing packets!
    Addr = nullResponse
    DataBack = nullResponse
    RegData0 = nullResponse
    RegData1 = nullResponse
    Tail = nullResponse
    Protocol = nullResponse

    if readWrite == 0:
      responseLength = 16
    else:
      responseLength = 16

    if response == 0:
      responseLength = responseLength
    else:
      responseLength = 10000*10

    a4=''
    a = SterlingCmdBuild(register, readWrite, data, response)
    for i in a.getCmd():
      a4 += chr(i)

    if self.__printCmd:
      print a.getCmd()

    # http://www.cyberciti.biz/faq/howto-get-current-date-time-in-python/
    if self.show_time:
      sendTime = datetime.now()
      print 'Packet Departure:', str(sendTime), sendTime.strftime('%Z')

    self.__UDPSock.sendto(a4,(self.__targetIP,self.__targetPort))

    if responseLength > 0:
      data,addr = self.__UDPSock.recvfrom(self.__receiveBuf)
#      if addr != self.__targetIP:
#        print "Reply did not originate from ", self.__targetIP, ",\n attempting to decode reply from ", addr, " anyway..."

      self.lastSerialNum = self.__packInt(data[0], data[1], data[2], data[3])
      self.lastWrite = (ord(data[4]) & 0x40) == 0x40
      self.lastAddress = self.__packInt(chr(0), data[5], data[6], data[7])
      self.lastData = self.__packInt(data[8], data[9], data[10], data[11])
      self.lastErrors = self.__packInt(chr(0), chr(0), data[12], data[13])
      self.lastTimeoutError = (self.lastErrors & 0x02) == 0x02
      self.lastOtherError = (self.lastErrors & 0x01) == 0x01
      self.lastTail = self.__packInt(chr(0), chr(0), data[14], data[15])

      if len(data) > 16:
        self.lastProtocol = 0
        for i in range( len(data)-16 ):
          self.lastProtocol = self.lastProtocol << 8
          self.lastProtocol = self.lastProtocol + ord(data[i+16])

      # Old Version 1.0 packet parsing 
#      for i in range(len(data)):
#        if( i == 3):
 #         SerNum = hex(((ord(data[i-3]))<<24)+((ord(data[i-2]))<<16)+((ord(data[i-1]))<<8)+((ord(data[i]))))
        #if( i == 4):
         #print 'Write/read ', ((hex(ord(data[i])) & 0x40) >>6)
#         print 'Write/read ', hex(ord(data[i]))
#        if( i == 7):
#          Addr = hex(((ord(data[i-2]))<<16)+((ord(data[i-1]))<<8)+((ord(data[i]))))
#        if( i == 11):
#          DataBack = hex(((ord(data[i-3]))<<24)+((ord(data[i-2]))<<16)+((ord(data[i-1]))<<8)+((ord(data[i]))))
#        if( i == 13):
#          RegData0 = (((ord(data[i-1]))<<8)+((ord(data[i]))))
#        if( i == 15):
#          RegData1 = (((ord(data[i-1]))<<8)+((ord(data[i]))))
#        if( i > 15):
#          Protocol = hex(ord(data[i]))

    # In the event of the terriby unlikely:
    if response:
      self.__waitForResponse()

    return {'SerNum': hex(self.lastSerialNum), 'Addr': hex(self.lastAddress),
      'Data': hex(self.lastData), 'Errors': hex(self.lastErrors),
      'Tail': hex(self.lastTail), 'Protocol': hex(self.lastProtocol)}

  def __packInt(self, byte0, byte1, byte2, byte3):
    '''Pack up string characters into 32-bit integer words.'''
    _byte0 = ord(byte0) << 24
    _byte1 = ord(byte1) << 16
    _byte2 = ord(byte2) << 8
    _byte3 = ord(byte3)
    return _byte0 + _byte1 + _byte2 + _byte3

  def read(self, register):
    '''Read the contents of the specified FPGA register.'''
    self.sendCmd(register, self.readRegister, self.readRegister,
                 self.responseFalse)
    if self.printPacketInfo > 1:
      print 'FPGA Reading Register:', hex(register)
      print 'Read', hex(self.lastData), 'from', hex(register)
    return self.lastData

  def write(self, register, value):
    '''Write the value to the specified FPGA register.'''
    if self.printPacketInfo > 1:
      print 'FPGA Writing', hex(value), 'to register', hex(register)
    self.sendCmd(register, self.writeRegister, value, self.responseFalse)

  def __del__(self):
    self.__UDPSock.close()

if __name__ == "__main__":
  import argparse
  import textwrap

  parser = argparse.ArgumentParser(
    description=textwrap.dedent('''\
    Use this program to send individual UDP packets to a CTA TARGET fpga and
    optionally display the response data.'''),
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog = textwrap.dedent('''\
    The core of this program is based on Leonid\'s PGPcmd_udp.py program, but 
    several modifications were made explicitly to allow this file to be a
    usable module for interfacing with the TARGET fpga programmatically.

    Written by Sterling Peet <sterling.peet@gatech.edu>, under
    Nepomuk Otte <http://otte.gatech.edu>
    Center for Relativistic Astrophysics
    Georgia Institute of Technology
    Atlanta, GA, USA'''), )
  parser.add_argument('-V', '--version', action='version',
    version='%(prog)s {version}, ({date})'.format(version=__version__,
    date=__date__))
  parser.add_argument('fpga_register', default=REG_0, nargs='?',
    help='Register of TARGET fpga to read/write.')
  parser.add_argument('data', default=DATA_0, nargs='?',
    help='The data value to write to the specified register.')
  parser.add_argument('response', default=RSP_NONE, nargs='?',
    help='Additional packet response, for trigger and calstrobe.')
  parser.add_argument('-w', '--write', action='store_true',
    help='Write to the register, rather than read.  Specifying this ' \
         'option overrides the default behavior of reading if VALUE is ' \
         'not provided, but writing if VALUE is provided.')
  group = parser.add_mutually_exclusive_group()
  group.add_argument('-v', '--verbose', action='count', default=0,
    help='Increase output verbosity.')
  group.add_argument('-q', '--quiet', action='count', default=0,
    help='Decrease output verbosity.')
  parser.add_argument('-i', '--show_time', action='store_true',
    help='Display the time when sending UDP packet.')
  parser.add_argument('-t', '--timeout', default=TIMEOUT,
    help='UDP packet timeout in seconds')
  parser.add_argument('--target_host', default=HOST,
    help='IP address of the TARGET fpga.')
  parser.add_argument("--target_port", default=PORT, type=int,
    help='Port the TARGET fpga is listening on.')
  parser.add_argument('--rx_port', default=PORT0, type=int,
    help='Local port to listen on for TARGET response packets.')
  parser.add_argument('-d', '--data_out', action='store_true',
    help='Use this flag if you want %(prog)s to return the data ' \
    'response as the exit code. (Useful for shell scripting)')
  parser.add_argument('-b', '--buffer_size', default=buffer, type=int,
    help='UDP buffer size.')

  args = parser.parse_args()

  if args.quiet < 1:
    print ""
    print "-" * 40
  if args.quiet < 2:
    print parser.prog, "( -h for usage )"
    print "-" * 40
  if args.verbose > 0:
   print "AGIS target assembly running on %s port %s" % (args.target_host,args.target_port)

  comm = FPGAcmd(args.target_host, args.target_port, HOST0, args.rx_port,
    eval(args.timeout), args.buffer_size)

  if args.show_time:
    comm.show_time = True;

  if args.write:
    readWrite = 1
  else:
    if eval(args.data) > 0:
      if eval(args.fpga_register) > 0:
        readWrite = 1
      else:
        readWrite = 0
    else:
      readWrite = 0

  if args.verbose > 0:
    print "\nOutgoing Packet Info:"
    if args.verbose > 2:
      print "Local Host Settings:", HOST0, "on port", args.rx_port
    if args.verbose > 1:
      print "R/W:", readWrite
    print "Register:", hex(eval(args.fpga_register))
    if readWrite:
      print "Data to Write:", hex(eval(args.data))
    if (args.verbose > 1) or (args.response != RSP_NONE):
      print "Response:", hex(eval(args.response))
    if args.verbose > 1:
      print "UDP rx timeout (sec):", args.timeout
    if args.verbose > 2:
      print "UDP rx buffer size:", args.buffer_size

  try:
    if args.verbose > 1:
      print "Packet Byte Array:"
      comm.setPrintCmd(True)
    result = comm.sendCmd(eval(args.fpga_register), readWrite, eval(args.data),
      eval(args.response))
    if args.verbose > 0:
      print "\nCommand Response Packet:"
      print "Serial Number:", result.get("SerNum")
    if (args.verbose > 1) or ((args.quiet < 2) and
                    (result.get("Errors") != "0x0")):
      print "Errors: ", result.get("Errors")
    if args.quiet < 1:
      print "Register:", result.get("Addr")
    if args.quiet < 1:
      print "Data:", result.get("Data")
    else:
      if args.quiet < 2:
        print result.get("Data")
    if args.verbose > 2:
      print "Tail:", result.get("Tail")
      print "Protocol:", result.get("Protocol")

  except timeout:
    if args.quiet < 3:
      print "\n***"
      print "*** Did not Recieve a valid response from the target within"
      print "*** the", args.timeout, "second timeout from %s on port %s." \
        % (args.target_host,args.rx_port)
      if args.verbose > 0:
        print "***"
        print "*** This could be caused by a lack of network connectivity,"
        print "*** possibly due to the phys43222 computer's network driver"
        print "*** problem (and thus the computer must be restarted)."
        print "*** It could also be caused by a disconnected fiber optic"
        print "*** cable, or the power to the FPGA could be faulty.  Check"
        print "*** the lights on the fiber network conversion box to ensure"
        print "*** they indicate a good connection."
      print "***\n"
    exit(1)

  if args.data_out:
    exit(eval(result.get('Data')))

