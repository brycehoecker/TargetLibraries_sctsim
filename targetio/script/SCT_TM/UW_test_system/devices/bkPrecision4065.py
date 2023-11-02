#!/usr/bin/env python
# Justin Vandenbroucke
# Created Apr 22 2015
# Example script to control BK Precision 4065 function generator (160 MHz arbitrary waveform generator).
# Uses pyvisa and requires National Instruments VISA to be installed.
# Similar to  Agilent33250A.py.

import pyvisa as visa

class bkPrecision4065(object):
	def __init__(self):
		libraryPath = '/Library/Frameworks/VISA.framework/VISA'
		rm = visa.ResourceManager(libraryPath)
		rm.list_resources()
		resource = 'USB0::0xF4ED::0xEE3A::448A15119::INSTR'
		self.instrument = rm.open_resource(resource)

	def sendCmd(self, command):
		self.instrument.write("%s" % command)

	def close(self):
		self.instrument.close()


if __name__ == "__main__":
	frequency = 20e6	# Hz
	amplitude = 1		# Vpp
	offset = 0		# V
	phase = 0		# deg

	bk = bkPrecision4065()
	bk.sendCmd('C1:OUTP OFF')
	bk.sendCmd('C1:BSWV WVTP,SINE')
	bk.sendCmd('C1:BSWV FRQ, %dHZ' % frequency)
	bk.sendCmd('C1:BSWV AMP, %fV' % amplitude)	# note this is peak to peak
	bk.sendCmd('C1:BSWV OFST, %f' % offset)
	bk.sendCmd('C1:BSWV PHSE, %f' % phase)
	#bk.sendCmd('C1:OUTP LOAD,HZ')			# load is high impedance
	bk.sendCmd('C1:OUTP LOAD,50')			# load is 50 ohm
	bk.sendCmd('C1:OUTP ON')

	bk.close()

