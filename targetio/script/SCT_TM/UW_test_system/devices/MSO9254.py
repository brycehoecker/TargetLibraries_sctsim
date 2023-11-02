# -*- coding: utf-8 -*-
"""
Created on Mon Jul 02 16:40:21 2018

@author: meures
"""

import visa
import numpy as np
import matplotlib.pyplot as plt
import re
import time
import os
import datetime
import sys


class MSO9254(object):
	def __init__(self):
        	self.status = True
	        self.rm = visa.ResourceManager()
		resource = "USB0::0x2A8D::0x900E::MY52090105::INSTR"
	        self.instrument = self.rm.open_resource(resource)
	        print(self.instrument.query("*IDN?"))
	        print("MSO9254 connected successfully!")
	def measureDelay(self):
		self.instrument.write("SYSTem:HEADer OFF")
		self.instrument.write("MEASure:DELTatime:DEFine RISing,1,MIDDle,RISing,1,MIDDle")
		self.instrument.write("MEASure:DELTatime CHANnel1,CHANnel3")
		dt = self.instrument.query("MEASure:DELTatime?")
		return dt
	def measureWidth(self):
		self.instrument.write("SYSTem:HEADer OFF")
		self.instrument.write("MEASure:DELTatime CHANnel3")
		dt = self.instrument.query("MEASure:DELTatime?")
		return dt

	def close(self):
		self.instrument.close()


	def sendcmd(self, cmd):
        	self.instrument.write("{}".format(cmd))

if __name__ == '__main__':
    exception = None
    fg = None
    try:
        fg = MSO9254()
        #fg.apply_pulse(1.0E3, 0.040, 0)
        #fg.sendcmd("PULS:WIDTH 5e-9")
        #fg.sendcmd("OUTP OFF")
        fg.close()
    except:
        exception = sys.exc_info()

    if exception:
        print("Failed to connect.")
        time.sleep(1)
        if fg:
            fg.close()
        raise SystemExit


"""
#Set trigger conditions:
#mso9254.write("TRIGger:MODE EDGE")
#print mso9254.query("TRIGger:MODE?")
#mso9254.write("TRIGger:EDGE:SOUrce CHANnel1")
#mso9254.write("TRIGger::LEVel {CHANnel1, 20e-3}")
#print mso9254.query("TRIGger:LEVel? CHANnel1")


#mso9254.write("CH2:SCAle 50e-3")


#print "Acquisition mode:", mso9254.query("ACQuire:STOPAfter?")
#print "Acquisition mode:", mso9254.query("ACQuire:MODE?")
#print "Acquisition state:", mso9254.query("ACQuire:STATE?")

#mso9254.write("ACQuire:STATE 1")
#print "Acquisition state:", mso9254.query("ACQuire:STATE?")


print "Accessible channels:", mso9254.query("SELect?")
tempChannels = mso9254.query("SELect?")
runChannels = map(int, re.findall(r'\d+', tempChannels))
print runChannels, tempChannels
#print runChannels[0]

print mso9254.query("WFMOutpre?")
nPoints = int(mso9254.query("HORizontal:ACQLENGTH?") )
#print "SAmpling interval:", mso9254.query("WFMOutpre:XINcr?")
xInterval = float(mso9254.query("WFMOutpre:XINcr?") )
#print "SAmpling Units:", mso9254.query("WFMOutpre:XUNit?")
mso9254.write("DATa:ENCdg ASCII")
times = np.arange(0,xInterval*nPoints,xInterval)

channel=1

mso9254.write("ACQuire:STOPAfter SEQUENCE")
start = time.time()

yScale=np.zeros(len(runChannels))
yOffset=np.zeros(len(runChannels))

currentDateAndTime = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
print currentDateAndTime

argList = sys.argv

if(len(argList)>1):
    directory = "acquisition_{}_{}/".format(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M"), argList[1])
else:
    directory = "acquisition_{}/".format(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M"))

if not os.path.exists("scopeCapture/TDA_40dB_LNA/"+directory):
    os.makedirs("scopeCapture/TDA_40dB_LNA/"+directory)

nEvents=20
for ev in range(nEvents):
    mso9254.write("ACQuire:STATE 1")
    newArray = times
    #for k in range(1,2):
    for k, ch in enumerate(runChannels):
        #print k, ch
     #   ch=1
     #if(k<3):
        if(int(ch)==1):
            mso9254.write("DATa:SOUrce CH{}".format(int(k+1)))
            #print mso9254.query("DATa:SOUrce?")
            #print "Y-axis scale factor:", mso9254.query("WFMOutpre:YMUlt?")
            if(ev==0):
                yScale[k] = mso9254.query("WFMOutpre:YMUlt?")
                yOffset[k] = mso9254.query("WFMOutpre:YZEro?")
            #print "Y-axis digitizing offset:", mso9254.query("WFMOutpre:YOFf?")
            #print "Y-axis unit:", mso9254.query("WFMOutpre:YUNit?")
            #print "Y-axis offset:", mso9254.query("WFMOutpre:YZEro?")

            #The Y-axis value is determined as: (Data*(Y-axis scale factor) + Y-axis offset)
            try:
                waveform = mso9254.query_ascii_values("CURVe?")
            except:
                continue
            waveform = np.array(waveform)*float(yScale[k]) + float(yOffset[k])
            #print times.shape, waveform.shape
            newArray = np.column_stack((newArray,waveform))
            #print newArray.shape, newArray[0:3]
            #print waveform[0:10], waveform[1]-waveform[2], np.max(waveform)

    np.savetxt('scopeCapture/TDA_40dB_LNA/{}/scope_test_file_ev{}.txt'.format(directory, ev), newArray)
    print "Wrote event file", ev
stop=time.time()

print "The elapsed time per iteration is: ", (stop-start  )*1.0/nEvents


#print mso9254.query("WAVFrm?")
"""
