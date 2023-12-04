#!/usr/bin/env python
# Thomas Meures
# Created July 11 2019
# Script to control Agilent MSO9254 oscilloscope..
# Uses pyvisa and requires National Instruments VISA to be installed.

import pyvisa as visa
import time, string, sys
#import logging


	
# Set constants
libraryPath = '/Library/Frameworks/VISA.framework/VISA'
resource = 'USB0::10893::36878::MY52090105::0::INSTR'

class AgilentMSO9254A(object):
	def __init__(self):
		rm = visa.ResourceManager(libraryPath)
		rm.list_resources()
		self.instrument = rm.open_resource(resource)
		result = self.instrument.query("*IDN?")
		if not result:
			print("ERROR: Could not find MSO9254A.  Make sure it is powered on.")
			sys.exit(1)
		else:
			print("Connected to Agilent MSO9265.")

	def close(self):
		self.instrument.close()

if __name__ == "__main__":

	scope = AgilentMSO9254A()
	scope.close()

