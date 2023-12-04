#!/usr/bin/env python
# Brent Mode
# Created 21 March 2019
# Script to control Agilent Infiniium MSO9254 Oscilloscope
# Uses pyvisa and requires National Instruments VISA to be installed.
# Similar to multishot.py written by Thomas Meures.

import time
import csv
import sys
import os
import string
import visa
import numpy as np
import scipy as sp

"""
This class controls the Agilent Infiniium MSO9254 Oscilloscope used in the Vandenbroucke lab. At this time (creation), we are using it to automate waveform sampling to characterize a temperature dependence in
the preupgrade camera modules for the pSCT. That said, for future projects and users, this class can be expanded to make other measurements and use other channels. Fewer settings could be hardcoded in, in particular
channel selection. The current amount of specification hardcoding was for ease-of-use for the current use case. YMMV. The current setup that this script works with is as follows. The scope is connected via ethernet to
a Buffalo wireless router's LAN port. The computer is connected to the router via ethernet to a different LAN port. I don't remember if we had to do anything specific to setup the router. We might have.
Ask Thomas if he's still here. If he's not, ask Leslie. If she's not, ask Brent. If he's not, then good luck because he wrote this software and can't get in trouble for this amount of unhelpfulness or sass. Cheers!
"""


class Scope():
	def __init__(self):
		ag9254Present = 0
		scopeDetect = 0
		rm = visa.ResourceManager() #Specifying @py is necesarry for the resource manager to find the scope.
		try:
			self.instrument = rm.open_resource("USB0::0x2A8D::0x900E::MY52090105::INSTR") #This is all static except for potentially the IP address. This can be checked on the scope by going to Utilities/Remote/ on the upper menu.
			ag9254Present = 1
			print(self.instrument.query("*IDN?"))
			print("Agilent MSO9254 connected successfully!")
			scopeDetect = 1
		except:
			if(ag9254Present == 0): #In event of failure (like forgetting to plug in the network connection), this will tell you which bit above pooped itself.
				print("Failed to find the scope.")
				sys.exit()
			if(scopeDetect == 1):
				print("Could not connect to scope.")
				sys.exit()

	def configure(self):
		self.instrument.timeout = 25000 #25 s in ms
		self.instrument.write("*CLS") #Clear screen
		self.instrument.write("*RST") #Reset settings

		#Select channels to view
		self.instrument.write(":VIEW CHAN1")
		self.instrument.write(":VIEW CHAN3")

		#Set time window: TIMEBASE scale is the division size
		self.instrument.write(":TIMEBASE:SCALE 20E-9") #Sets the grid spacing of the x-axis (time) in seconds.
		self.instrument.write(":TIMEBASE:REFERENCE CENTER")

		#Trigger settings:
		self.instrument.write(":TRIGGER:MODE EDGE")
		self.instrument.write(":TRIGGER:SWEEP TRIG")
		#self.instrument.write(":TRIGGER:EDGE:SOURCE CHAN1")
		#self.instrument.write(":TRIGGER:EDGE:SLOPE POSITIVE")
		#self.instrument.write(":TRIGGER:LEVEL CHANNEL1, 0.50") #Sets the Trigger level for the specified channel in Volts.
		self.instrument.write(":TRIGGER:EDGE:SOURCE CHAN3")
		self.instrument.write(":TRIGGER:EDGE:SLOPE POSITIVE")
		self.instrument.write(":TRIGGER:LEVEL CHANNEL3, 0.050")

		self.instrument.write(":CHANNEL3:RANGE 0.400") #Sets total voltage range (max voltage - min voltage) in Volts.
		self.instrument.write(":CHANNEL1:RANGE 0.800")
		#self.instrument.write(":ACQUIRE:MODE RTIME") #Set to acquire waveforms in real time.
		#self.instrument.write(":ACQUIRE:AVERAGE ON") #Turn on waveform averaging. Not entirely sure this is doing anything. Need to confirm.
		#self.instrument.write(":ACQUIRE:AVERAGE:COUNT 10") #Sets the number of waveforms to average. Again, there's a noticeable time delay that is dependent on this setting, but it's not clear if it's actually influencing measurement.
		#self.instrument.write(":WAVEFORM:FORMAT BYTE") #Sets the format for waveform acquisition to signed 8-bit ints. We would use ASCII but it gets hung up a lot. THIS MEANS THAT WE DON'T GET VOLTS. WE GET "QUANTIZATION UNITS". Have to convert to volts if that's necessary then. For us, right now, it doesn't seem to be.
		print("Scope successfully configured!")

	def waveform_save(self,wavefile):
		self.instrument.write(":WAVEFORM:SOURCE CHANNEL1") #Set the waveform to be acquired.
		self.instrument.write(":ACQUIRE:POINTS 100") #Supposedly sets the number of data points acquired to describe the waveform. Depending on format setting, this can vary drastically. ASCII is especially weird. Seems to increase time integration for waveform acquisition but not resolution.
		self.instrument.write(":DIGITIZE CHANNEL1") #This freezes everything and tells the oscilloscope to hoover up all of the waveform values. This is when the averaging happens, but doesn't seem to change the waveform collected. Odd.
		t = str(time.time())
		values = self.instrument.query_binary_values(":WAVEFORM:DATA?", datatype='i', is_big_endian=False) #Downloads the waveform from the scope. Data type is 8 bit signed int and the endianness doesn't seem to affect the final result.
		#values /= 2 ** 24 #Ok, so using the BYTE format and querying binary values tells the oscilloscope to take in its 16 bit int data, truncate it, and download an 8 bit signed int to computer. Python is dumb and reads this as a 32 bit signed int, where the first 8 bits are what we want, and the next 24 are 0's. So we chop those off here.
		filename = wavefile + "_1_" + t + ".csv" #The format here is, specifiedFilename_channelNumber_timeSinceUTCEpoch.csv. This automation isn't as clean as it could be, but filenames are unique. Works for now.
		f = open(filename, "w")
		for value in values:
			f.write(str(value) + '\n')
		f.close()

		self.instrument.write(":WAVEFORM:SOURCE CHANNEL3") #Same as before for Channel 3, instead of Channel 1.
		self.instrument.write(":ACQUIRE:POINTS 100")
		self.instrument.write(":DIGITIZE CHANNEL3")
		values = self.instrument.query_binary_values(":WAVEFORM:DATA?", datatype='i', is_big_endian=False)
		filename = wavefile + "_3_" + t + ".csv"
		f = open(filename, "w")
		for value in values:
			f.write(str(value) + '\n')
		f.close()


	def configure_delta_time(self):
		self.instrument.write(":MEASURE:SOURCE CHANNEL1, CHANNEL3")
		#self.instrument.write(":ACQUIRE:AVERAGE ON")
		#self.instrument.write(":ACQUIRE:AVERAGE COUNT 1000")
		self.instrument.write(":SYSTEM:HEADER OFF")
		self.instrument.write(":MEASURE:DELTATIME:DEFine RISing, 1, MIDDle, RISing, 1, MIDDle")
		self.instrument.write(":MEASURE:DELTATIME CHANNEL1, CHANNEL3") #Take the measurement.

	def measure_delta_time(self):
		value = self.instrument.query_ascii_values(":MEASURE:DELTATIME?") #Download the measurement
		return(value)

	def measure_pulse_width_ch1(self):
		self.configure()
		self.instrument.write(":MEASURE:SOURCE CHANNEL1")
		self.instrument.write(":ACQUIRE:AVERAGE ON")
		self.instrument.write(":ACQUIRE:AVERAGE COUNT 1000")
		self.instrument.write(":MEASURE:PWIDTH CHANNEL1")
		value = self.instrument.query_ascii_values(":MEASURE:PWIDTH?")
		return(value)

	def measure_pulse_width_ch3(self):
		self.configure()
		self.instrument.write(":MEASURE:SOURCE CHANNEL3")
		self.instrument.write(":ACQUIRE:AVERAGE ON")
		self.instrument.write(":ACQUIRE:AVERAGE COUNT 1000")
		self.instrument.write(":MEASURE:PWIDTH CHANNEL3")
		value = self.instrument.query_ascii_values(":MEASURE:PWIDTH?")
		return(value)

	def configure_pulse_width(self):
		#self.instrument.write(":MEASURE:SOURCE CHANNEL1")
		self.instrument.write(":MEASURE:PWIDTH CHANNEL1")

	def measure_pulse_width(self):
		value = self.instrument.query_ascii_values("MEASURE:PWIDTH?")
		return(value)

	def close(self):
		self.instrument.close()

