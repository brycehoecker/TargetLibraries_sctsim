#!/usr/bin/env python
# Justin Vandenbroucke
# Created May 20 2013
# Script to control the Agilent 33250A function generator.
# User manual for the FG can be found on the web.
# Commands listed here can be used as example commands - these and more are listed and described in the user manual.
# The FG is connected by serial connection (on the mac, a serial to usb converter is also necessary).

import time, serial, sys

class Agilent33250A(object):
	def __init__(self):
		self.ser = serial.Serial(port='/dev/tty.usbserial',
#		self.ser = serial.Serial(port='/dev/tty.Bluetooth-Modem',
                                 baudrate=115200,
                                 bytesize=8,
                                 parity='N',
                                 stopbits=1,
                                 timeout=1,
                                 writeTimeout=1,
                                 dsrdtr=1)
		time.sleep(0.05)
		self.ser.write("OUTP OFF\n")
		time.sleep(0.1)

	def sendCmd(self, command):
		self.ser.write("%s\n" % command)
		time.sleep(0.1)

	def close(self):
		self.ser.close()


if __name__ == "__main__":
	fg = Agilent33250A()
	fg.sendCmd('OUTP ON')
	print "Enabled output"
	time.sleep(1)
#	fg.sendCmd("OUTP OFF")
	# set up interface with the Agilent 33250A FG
#	fg = Agilent33250A()
#	fg.sendCmd("FUNC SIN")
#	fg.sendCmd("garbage")
#	fg.sendCmd("FUNC PULS")
#	fg.sendCmd("FUNC:SHAP PULS")
#	fg.sendCmd("FUNC:SHAP SIN")

#	fg.sendCmd("OUTP:SYNC ON")
#	fg.sendCmd("OUTP:LOAD 50")
#	fg.sendCmd("OUTP:POL NORM")
#	fg.sendCmd("VOLT:UNIT VPP")	# choices are VPP, VRMS, VBM
#	fg.sendCmd("FREQ 80000000")
#	fg.sendCmd("PULS:PER 0.000000064")
	# Configure voltage with high and low levels
#	fg.sendCmd("VOLT:LOW 0")
#	fg.sendCmd("VOLT:HIGH 0.5")

	# Choose whether burst mode is enabled or not
#	fg.sendCmd("BURST:STATE OFF")
	fg.sendCmd("BURS:STATE ON")
	fg.sendCmd("BURS:NCYC 1")
	fg.sendCmd("BURS:MODE TRIG")
#	fg.sendCmd("TRIG:SOUR IMM")
	fg.sendCmd("TRIG:SOUR EXT")
#	fg.sendCmd("BURS:INT:PER 0.001")
#	fg.sendCmd("TRIG:DEL .000000100") # sec
	fg.sendCmd("TRIG:DEL 0.000000050") # sec
#	fg.sendCmd("VOLT 1.0")	# Vpp
#	fg.sendCmd("VOLT 0")	# Vpp
#	fg.sendCmd("VOLTAGE:OFFSET 0")

	# Configure voltage with offset and amplitude
#	fg.sendCmd("VOLT:OFFS 0.0")

#	ampList = [1,10,100,1000]	# mV
#	ampList = [800]			# mV
#	ampList = [1]
#	mVPerV = 1e3
#	ampList = [1.0]		# mV
#	ampList = [0]
#	for amp in ampList:
#		print "Setting amplitude to %d mV." % amp
#		fg.sendCmd("VOLT %f" % (amp/mVPerV))
#		time.sleep(1)
	fg.close()
	time.sleep(1)
