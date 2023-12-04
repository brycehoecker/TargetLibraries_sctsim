#!/usr/bin/env python

import time, serial, sys

class LED(object):
        def __init__(self):
                self.ser = serial.Serial(port='/dev/tty.usbserial',
#               self.ser = serial.Serial(port='/dev/tty.Bluetooth-Modem',
                                 baudrate=9600,
                                 bytesize=8,
                                 parity='N',
                                 stopbits=1)
                time.sleep(0.05)
                self.ser.write("ALL OFF\n")
                time.sleep(0.1)

        def sendCmd(self, command):
                self.ser.write("%s\n" % command)
                time.sleep(0.1)

        def close(self):
                self.ser.close()
	

	"""
	freq: frequency in Hz
	trig_output: boolean to decide whether we want trigger output on or off
	flasher_output: boolean for flasher on or off
	"""
	def setLED(self, freq, trig_output, flasher_output):
		if trig_output:
			self.sendCmd("TRIG_OUTPUT ON") #5V pulse, used to trigger a laser when not using the LED
		else:
			self.sendCmd("TRIG_OUTPUT OFF")
		if flasher_output:
			self.sendCmd("FAST_PULSE ON") #LED2, about 3ns FWHM
			
			# set parameters
			self.sendCmd("FREQ {}".format(freq)) # in Hz
			self.sendCmd("BRIGHTNESS 4095") # 0...4095
			self.sendCmd("AWG_SET 100") # Set AWG waveform with 100 samples, one per 10ns bin
		else: 
			self.sendCmd("FAST_PULSE OFF")
			
	def LEDoff(self):
		self.sendCmd("ALL OFF")
		self.close()
		time.sleep(1)

if __name__ == "__main__":

	ld = LED()

	## Set pulse length (width adjusted by screws in the box)
	#ld.sendCmd('LONG_PULSE ON') # LED1, 1microsec length
	#ld.sendCmd('STANDARD_PULSE ON') # LED1, 30ns length
	#ld.sendCmd('FAST_PULSE ON') # LED2, about 3ns FWHM

	## Set parameters
	#ld.sendCmd("FREQ 100") # in Hz
	#ld.sendCmd("BRIGHTNESS 4095") # 0...4095
	#ld.sendCmd("AWG_SET 100") # Set AWG waveform with 100 samples, one per 10ns bin

	## Output (Default all off)
	#ld.sendCmd("TRIG_OUTPUT ON") # 5V pulse,used to trigger a laser when not using the LED
	#ld.sendCmd("SYNC_OUTPUT ON") # negative going low amplitude pulse, provide a reference time for LED pulse
	#ld.sendCmd("RELAY ON")
	time.sleep(5)
	ld.setLED(100,1,1)
	time.sleep(5)
	ld.LEDoff()
	time.sleep(5)
	ld.setLED(200,1,0)
	ld.LEDoff()
	#time.sleep(10)

	## switch off the LED
	#ld.sendCmd("ALL OFF")

	ld.close()
	time.sleep(1)	
