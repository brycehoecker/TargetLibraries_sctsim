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


now = datetime.datetime.now()
outdirname = now.strftime("%m%d%y")

argList = sys.argv

if(len(argList)>2):
	start = int(argList[1])
	stop = int(argList[2])
elif(len(argList)>1):
	start = int(argList[1])
	stop = start
else:
	start = 292836
	stop = 292836
print argList
print start, stop
irgList = sys.argv
#runList = [286575,286576,286577,286578]

#runList = range(286868,286878+1)

#runList = range(286811,286860+1)

runList = range(start,stop+1)

for runID in runList:

	homedir = os.environ['HOME']
	hostname = run_control.getHostName()
	indirname = "/data/local_outputDir/"
##	filename = indirname+"runs_300000_through_309999/run{}.fits".format(runID)
	filename = indirname+"run{}.fits".format(runID)
	backupfn = homedir+"/target5and7data/run{}.fits".format(runID)
	print "Reading file: ", filename
##	filename = "/Users/tmeures/target5and7data/run%d.fits" % (runID)

#	while(not( os.path.isfile(filename))):
#		time.sleep(1)	

	numModules = 15
	chPerPacket = 16
	numBlocks = 2
	nSamples = numBlocks*32
	nchannel = 16
	nasic = 4*numModules
	reader = target_io.EventFileReader(backupfn)
	nEvents = reader.GetNEvents()
	print "number of events", nEvents
	rawdata = reader.GetEventPacket(0,0)
	packet = target_driver.DataPacket()
        packet.Assign(rawdata, reader.GetPacketSize())
	print "The Packet size is: ", reader.GetPacketSize()
        wf = packet.GetWaveform(0)
	nSamples = wf.GetSamples()
	print "Number of samples: ", wf.GetSamples()
	numBlocks = nSamples/32
	"""
	if(nEvents>300):
#		print "Plot only first 300 events!"
		nEvents=100
	"""

	packetHist = [0]*( (nasic*nchannel)/chPerPacket)
	eventHist = []
	fig = plt.figure(figsize=(9,9))
	ax = fig.add_subplot(211)
	ax2 = fig.add_subplot(212)

	#for asic in range(nasic):
	for packetInd in range( (nasic*nchannel)/chPerPacket):
		for ievt in range(0,nEvents):
			rawdata = reader.GetEventPacket(ievt, packetInd)
			packet = target_driver.DataPacket()
			packet.Assign(rawdata, reader.GetPacketSize())
			packetID = packet.GetPacketID()
			if not packetID[0]:
				packetHist[packetInd]+=1
				eventHist.append(ievt)
	
	from collections import OrderedDict
	badEvents = OrderedDict((x, True) for x in eventHist).keys()
	
	N = len(packetHist)
	x = range(N)
	ax.bar(x, packetHist)
	ax.set_title("Run {}, {} Modules, {} Ch/Packet, {} Events".format(runID,numModules, chPerPacket, nEvents))
	ax.set_xlim(0,N)
	ax.set_xlabel("Packets")
	ax.set_ylabel("Lost Event Packets")
	
	ax2.hist(eventHist, bins=np.arange(0,nEvents,nEvents/250))
	ax2.set_xlabel("Event of packet loss")
	ax2.set_ylabel("Packets lost")

	fig1 = plt.figure(figsize=(9,6))
	axfig1 = fig1.add_subplot(111)
	
	packetsPerMod = []
	for i in range(numModules):
		packetsPerMod.append(sum(packetHist[i*4:i*4+4]))
	modInds = range(numModules)
	axfig1.bar(modInds, packetsPerMod)
	axfig1.set_title("Run {}, {} Modules, {} Ch/Packet, {} Events".format(runID, numModules, chPerPacket, nEvents))
	axfig1.set_xlim(0,numModules)
	axfig1.set_xlabel("Module index")
	axfig1.set_ylabel("Lost event packets")

	saveDir = "%s/Pictures/%s" % (homedir, outdirname)
	try:
		os.mkdir(saveDir)
	except:
		print "Directory couldn't be created: %s." % saveDir
	fig.savefig('{}/run{}_{}blocks_packetLoss.png'.format(saveDir, runID, numBlocks))
	fig1.savefig('{}/run{}_module_packetLoss.png'.format(saveDir, runID))
	print packetHist, N, sum(packetHist)

	print
	print "num of bad events", len(badEvents)
	print "num of events", nEvents
	print "# packets dropped", len(eventHist)
	
	print "{:.2f}% of events are bad".format(100*float(len(badEvents))/nEvents)
#plt.show()
