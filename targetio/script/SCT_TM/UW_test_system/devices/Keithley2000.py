#!/usr/bin/env python
# Miles Winter
# Created Aug 16 2017
# Read voltage from Keithley 2000.
# Note: signal should be connected to the front right terminals of Keithley.
# Keithley should also be configured appropriately for serial.
# Voltage is returned in Volts.
# Requires the pyserial module to be installed: http://pyserial.sourceforge.net/

import serial, sys, time
import numpy as np

class Keithley2000:
	def configure(self,readMode='voltage'):
                print 'Opening Serial Port and Connecting to Keithley 2000 Multimeter'
		self.ser = serial.Serial(port="/dev/tty.usbserial",baudrate=19200,timeout=1,writeTimeout=1)
                self.readMode = readMode
                #self.ser.write(':SYST:REM\n')
		if self.readMode=='voltage':
			#self.ser.write(':SENS:FUNC "Volt"\n')			# set sensor type to voltmeter
                        #self.ser.write(':CONF:VOLT\n')
                        #self.ser.write(':READ?\n')
                        self.ser.write(':MEAS:VOLT?\n')
		elif self.readMode=='current':
			self.ser.write(':SENS:FUNC "Amp"\n')			# set sensor type to ammeter
		else:
			print "ERROR: unknown read type (%s).  Exiting."
			sys.exit(1)	
                #self.ser.write(':DISP:ENAB 0\n')
	def read(self):
                #self.ser.write(':READ?\n')
                #self.ser.write(':MEAS:VOLT?\n')
		if self.readMode== 'voltage':
                        self.ser.write(':MEAS:VOLT?\n')
                        #self.ser.write(':READ?\n')
                        voltage = self.ser.readline()
                        while True:
                            if len(voltage) == 18:
                                break
                            else:
                                self.ser.write(':MEAS:VOLT?\n')
                                #self.ser.write(':READ?\n')
                                voltage = self.ser.readline()
                        self.voltage = float(voltage[2:-2])
		elif self.readMode=='current':
			self.current = float(self.ser.readline().split(',')[0])	# Amps
        def close(self):
                print 'Disconnecting Keithley 2000 Multimeter and Closing Serial Port'
                self.ser.write(':SYST:LOC\n')
                time.sleep(1)
                self.ser.close()

if __name__ == "__main__":
	keith = Keithley2000()
	keith.configure(readMode='voltage')
        for i in range(5):
	    keith.read()
	    voltage = keith.voltage
            print voltage
            time.sleep(2)
        keith.close()
