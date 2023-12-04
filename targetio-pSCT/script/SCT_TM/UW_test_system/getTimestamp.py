import target_io
import target_driver
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec
import datetime
import time
import sys
import os
import run_control
from ctypes import c_longlong
nModules = 1

now = datetime.datetime.now()
outdirname = now.strftime("%m%d%y")
"""
argList = sys.argv
if(len(argList)>3):
	start = int(argList[1])
	stop = int(argList[2])
	nModules = int(argList[3])
elif(len(argList)>2):
	start = int(argList[1])
	stop = int(argList[2])
	nModules=1
elif(len(argList)>1):
	start = int(argList[1])
	stop = start
	nModules=1
else:
	start = 292836
	stop = 292836
print argList
print start, stop
irgList = sys.argv
#runList = [286575,286576,286577,286578]
"""
def GetChannelsPerPacket(PacketSize, nSamples):
    cpp = (0.5*PacketSize-10.)/(nSamples+1.)
    return int(cpp)
#runList = range(286868,286878+1)

#runList = range(286811,286860+1)

#runList = range(start,stop+1)

#runList = range(326549, 326613+1)
runList = [2]
for runID in runList:

    homedir = os.environ['HOME']
    hostname = run_control.getHostName()
    indirname = run_control.getDataDirname(hostname)
#	filename = indirname+"runs_310000_through_319999/run{}.fits".format(runID)
	#filename = indirname+"run{}.fits".format(runID)
    #a = int(sys.argv[2])
    c = int(sys.argv[2])
    filename = sys.argv[1]
    print "Reading file: ", filename
##	filename = "/Users/tmeures/target5and7data/run%d.fits" % (runID)

#	while(not( os.path.isfile(filename))):
#		time.sleep(1)

    nSamples = 8*32
    nchannel = 16
    nasic = 4*nModules
    print "The number of ASICs involved: ", nasic
    reader = target_io.EventFileReader(filename)
    nEvents = reader.GetNEvents()
    print "number of events", nEvents
    rawdata = reader.GetEventPacket(0,0)
    packet = target_driver.DataPacket()
    packet.Assign(rawdata, reader.GetPacketSize())
    print "The Packet size is: ", reader.GetPacketSize()
    wf = packet.GetWaveform(0)
    nSamples = wf.GetSamples()
    PacketSize = reader.GetPacketSize()
    timestamp = packet.GetTACKTime();
    print "got timestamp: ", timestamp
    chPerPacket = GetChannelsPerPacket(PacketSize,nSamples)
    print "Number of samples: ", wf.GetSamples()
    print "Channels per packet are:", chPerPacket


    startEvents = 0
    
    for asic in range(0, 1):
        for channel in range(1):
	    f = open("rateTest_timestamp_threhs{}.txt".format(c), 'w')
            for ievt in range(nEvents):
		if(ievt%1000==0):
				sys.stdout.write('\r')
				sys.stdout.write("[%-100s] %d%%" % ('='*int((ievt-startEvents)*100.0/(nEvents-startEvents)) , (ievt-startEvents)*100.0/(nEvents-startEvents)))
				sys.stdout.flush()

                rawdata = reader.GetEventPacket(ievt,(asic*nchannel)/chPerPacket+(channel/chPerPacket))
                packet = target_driver.DataPacket()
                packet.Assign(rawdata, reader.GetPacketSize())
                header = target_driver.EventHeader()
                reader.GetEventHeader(ievt, header);
                #sec = 0
                #nanosec = 0
                #header.GetTimeStamp(&sec, &nanosec)
		timestamp = packet.GetTACKTime();
		f.write("%d   %d \n" % (ievt, timestamp))


	    f.close()

#plt.show()
