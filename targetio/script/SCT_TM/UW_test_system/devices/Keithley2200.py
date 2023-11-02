#!/usr/bin/env python
# Justin Vandenbroucke
# Created Aug 26 2015
# Script to control Keithley 2200 power supply.
# Uses pyvisa and requires National Instruments VISA to be installed.
# Similar to  bkPrecision4065.py.

import pyvisa as visa
import time, string, sys
#import logging



# Set constants
libraryPath = '/Library/Frameworks/VISA.framework/VISA'
resource = 'USB0::0x05E6::0x2200::9050140::INSTR' #Whitney

class Keithley2200(object):
	def __init__(self):
		rm = visa.ResourceManager()
		rm.list_resources()
		self.instrument = rm.open_resource(resource)
		result = self.instrument.query("*IDN?")
		if not result:
			print("ERROR: Could not find Keithley 2200.  Make sure it is powered on.")
			sys.exit(1)
		else:
			print("Connected to Keithley 2200.")

	def sendCmd(self, command):
		return self.instrument.write('%s' % command)

	def close(self):
		self.instrument.close()

	def setV(self, volt):			#use decimals (ex keithley.setV(1.0) )
		self.sendCmd('SOURCE:Volt %s V' % volt)
		time.sleep(1)	#give it time to settle

	def setI(self, current):		#use decimals (ex keithley.setI(1.0) )
		self.sendCmd('SOURCE:Current %s A' % current)
		time.sleep(1)	#time to settle

	def setOutput(self, outputSwitch):	#use ON/OFF (ex keithley.setOutput('ON') )
		self.sendCmd('SOURCE:Output %s' % outputSwitch)

	def readV(self):			#use keithley.readV()
		self.sendCmd('MEASURE:Volt?')
		return self.instrument.read()

	def readI(self):			#use keithley.readI()
		self.sendCmd('MEASURE:Current?')
		return self.instrument.read()


	def powerModuleOn(self):

		self.setOutput('OFF')
		#keithley.setV(1.0)
		time.sleep(3)
		self.setV(12)
		self.setI(4.0)

		self.setOutput('ON')
		time.sleep(0.5)
	#	print keithley.readV()
	#	print keithley.readI()
		message = self.readV()
		print "Voltage is:",message
		message = self.readI()
		print "Current is:", message

	def powerModuleOff(self):

		self.setOutput('OFF')
		#keithley.setV(1.0)
		time.sleep(0.5)
		message = self.readV()
		print "Voltage is:",message
		message = self.readI()
		print "Current is:", message

if __name__ == "__main__":

	keithley = Keithley2200()
	keithley.setOutput('OFF')
	#keithley.setV(1.0)

	#keithley.setV(12)
	time.sleep(1)
	#keithley.setOutput('ON')
	#keithley.setI(2.0)
#	print keithley.readV()
#	print keithley.readI()
	message = keithley.readV()
	print message
	#logging.debug(message)
	message = keithley.readI()
	print message


	#time.sleep(3)

	#keithley.setOutput('OFF')


	#logging.debug(message)
	keithley.close()

