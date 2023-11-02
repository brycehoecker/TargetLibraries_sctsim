""" 
    Device Control - Motion Stage
    Class implementation of serial-controlled motion stage
    
    CVS $Id: PowerSupply.py,v 1.1.1.1 2009/01/22 01:26:00 philiph Exp $
    Philip Hart
    PhilipH@slac.stanford.edu
    
"""
import time
import serial
import Keithley2200
#import logging

VoltageTolerance = 0.1

def quit():
    shell.close()    
    sys.exit(0)
    
class BrickPowerSupply(object):
    # defaults: type = '2200', port = ''
    def __init__(self, type, port):
        self.__type = type
        self.__port = port
        self.__sleepTime = 0.1
        if type == '1786' or type == '1787':
            self.__getString = "GETD"
            self.__setVString = 'VOLT'
            self.__setIString = 'CURR'
            self.__parseLength = 7
            self.__responseLength = 3 ## need to check
        elif type == '1697':	# for now setting variables for 2200 as if it is 1697 -- can correct later
            self.__getString = "GETD00"
            self.__setVString = 'VOLT00'
            self.__setIString = 'CURR00'
            self.__parseLength = 9
            self.__responseLength = 2
        elif type == '2200':		# this is all serial connection stuff, pass if using keithley
		self.keithley = Keithley2200.Keithley2200()
	#	logging.info( self.keithley )
	#	logging.info( "finished constructor" )
		pass
	else:
            raise RuntimeError, 'type %s not recognized - required to define BrickPowerSupply' %(type)

    def open(self):
	if self.getType() == '2200':		#initialize keithley
		self.keithley = Keithley2200.Keithley2200()
	else:
        	self.__ser = serial.Serial(self.__port)
	print("Power supply is model %s.", self.__type)

    def close(self):
        if self.getType() == '2200':
		self.keithley.close()
	else:
		self.write("ENDS00")
        	self.__ser.close()

    def write(self, cmd):
        self.clear()
##        print "writing %s\n" %(cmd+"\r")
        self.__ser.write(cmd+"\r")
        time.sleep(self.__sleepTime)

    def read(self):
        status = self.__ser.read(self.__ser.inWaiting())
        time.sleep(self.__sleepTime)
        output = status.split()
##        print "output in read:", status, output
        if output == [] or type(output) != type([]) or len(output) != self.__responseLength:
            if output == []:
                raise RuntimeError, 'unparseable serial output []'
            raise RuntimeError, 'unparseable serial output %s' %(output)
        if self.__responseLength == 3:
            output.pop(0)
        if self.__responseLength >= 2:
            if output[1] != 'OK':
                raise RuntimeError, 'serial output is not OK, find %s' %(output[1])
        return output[0]

    def setup(self): 		#don't need to run for keithley, just call outputOn() instead
        self.write("SESS00")
        try:
            self.write(self.__getString) # first write fails under some circumstances
            self.pause()
            self.read()
            self.pause()
            self.read()
        except:
##            print "except in setup read, continue"
            pass
        return True
        return self.outputOn()

    def outputOn(self):
	if self.getType() == '2200':		#sets keithley output on
		self.keithley.setOutput('ON')
		return True
        elif self.getType() != '1697':
            return False
        self.write("SOUT010")
        (v, i) = self.getVoltageCurrent()
        if i == 0.:
            return False
        return True

    def outputOff(self):
	if self.getType() == '2200':		#sets keithley output off
		self.keithley.setOutput('OFF')
		return True
        elif self.getType() != '1697':
            return False
        self.write("SOUT011")
        return True

    def setVoltage(self, voltage):
	if self.getType() == '2200':	# accommodation for keithley PS
		self.keithley.setV(voltage)
		readV = self.keithley.readV()
		output2200 = self.getVoltageCurrent()
		#check to make sure the output voltage is close enough to the voltage it was set with
		if not output2200 == False:
			return abs(float(output2200[0]) - voltage) < VoltageTolerance
		return False

        voltDec = int(round(voltage*10))
        if voltDec < 10:
            voltStr = '00' + str(voltDec)
        elif voltDec < 100:
            voltStr = '0' + str(voltDec)
        else:
            voltStr = str(voltDec)
        setStr = self.__setVString + voltStr
        self.write(setStr)
        if self.getType() == '1786' or self.getType() == '1787':
            self.clear()
    
        output = self.getVoltageCurrent()
        if not output == False:
            return abs(output[0] - voltage) < VoltageTolerance
        return False

    def setMaxCurrent(self, current):
	if self.getType() == '2200':		#passing for now, doesn't appear to be a way to set the max current on keithley
		print "Warning: max current has not been set to %f A, as requested.  Cannot set max current in software with Keithley 2200." % current
		return True
        currHun = int(round(current*100))
        if currHun < 10:
            currStr = '00' + str(currHun)
        elif currHun < 100:
            currStr = '0' + str(currHun)
        else:
            currStr = str(currHun)
        setStr = self.__setIString + currStr
        self.write(setStr)
        if self.getType() == '1786' or self.getType() == '1787':
            self.clear()


    def getVoltageCurrent(self):
	if self.getType() == '2200':		#accommodation for keithley PS
		keithVol = float(self.keithley.readV())
		keithCur = float(self.keithley.readI())
		return (keithVol, keithCur)	#returns the voltage and current for keithley PS

        if self.__getString is None:
            return False
        parseLength = self.__parseLength

        self.write(self.__getString)
        output = self.read()
        output = output.split('\r')[0]
##        print output
        if not output:
            print 'no output found in BrickPowerSupply'
            return False
        if len(output) != parseLength:
            print 'problem in gVC', output ## tmp
            print 'output %s: length %d, expected %d in BrickPowerSupply' %(output, len(output), parseLength)
            return False
        if parseLength == 7:
            vChar = 3
            vScale = 10.
            iChar = 4
            iScale = 100.
            endChar = parseLength - 1
        else:
            vChar = 4
            vScale = 100.
            iChar = 4
            iScale = 100.
            endChar = parseLength - 2

        if output[:vChar].lstrip('0') == '':
            vSet = 0.
        else:
            vSet = eval(output[:vChar].lstrip('0'))/vScale ## string.atoi(output[:vChar])/vScale
        if output[iChar:endChar].lstrip('0') == '':
            iSet = 0.
        else:
##            print iScale, output[iChar:endChar], eval(output[iChar:endChar]),eval(eval(output[iChar:endChar])) 
            iSet = eval(output[iChar:endChar].lstrip("0"))/iScale
        return (vSet, iSet)

    def checkCurrent(self,Imin,Imax,waiting_time,sleep_time=5):
	if self.getType() == '2200':	# for keithley, checking if current is in a good place
		I = float(self.keithley.readI())
		V = float(self.keithley.readV())	# V
		if I>Imin and I<Imax:	#current between Imin and Imax
			return (True,V,I)
		else:
			return (False,V,I)
	 
        tstart=time.time()
        elapsed=0.
        (V,I)=self.getVoltageCurrent()
        while elapsed<waiting_time and I<Imin:
            time.sleep(sleep_time)
            elapsed=time.time()-tstart
            (V,I)=self.getVoltageCurrent()

        if I>Imin and I<Imax:
            return (True,V,I)
        else:
            return (False,V,I)
    

    def clear(self): ## move to base class?
        try:
            self.read()
            self.pause()
        except:
##            print "clear sees nothing"
            pass
        
    def pause(self): ## move to base class
        time.sleep(self.__sleepTime)

    def getType(self):
        return self.__type

##    def read(self):
##        rawOutput = super(PowerSupply, self).read()
##        return rawOutput.split('\\')[0]

if __name__ == "__main__":

    bps = BrickPowerSupply('2200','/dev/tty.usbserial')
    bps.open()
    bps.outputOn()
#    bps.setup()
    print "try to set voltage"
    #bps.setVoltage(5)
    print "have set voltage"
    print 'get voltage, current:', bps.getVoltageCurrent()
    bps.outputOn()
    #bps.outputOff()
    time.sleep(7)
    print 'get voltage, current:', bps.getVoltageCurrent()
    print bps.checkCurrent(0.6,0.8,60)
    bps.close()
    
