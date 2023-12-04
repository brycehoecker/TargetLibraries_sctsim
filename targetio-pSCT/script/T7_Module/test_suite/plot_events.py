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

#runList = range(286868,286878+1)

#runList = range(286811,286860+1)

runList = range(start,stop+1)

for runID in runList:

	homedir = os.environ['HOME']
	hostname = run_control.getHostName()
	indirname = run_control.getDataDirname(hostname)
##	filename = indirname+"runs_300000_through_309999/run{}.fits".format(runID)
	filename = indirname+"run{}.fits".format(runID)
	print "Reading file: ", filename
##	filename = "/Users/tmeures/target5and7data/run%d.fits" % (runID)

#	while(not( os.path.isfile(filename))):
#		time.sleep(1)	

	nSamples = 8*32
	nchannel = 16
	chPerPacket = 8
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
	print "Number of samples: ", wf.GetSamples()
	if(nEvents>500):
#		print "Plot only first 300 events!"
		nEvents=250

	ampl = np.zeros([nEvents+1000,nasic, nchannel, nSamples])
	for asic in range(nasic):
	#for asic in range(1):
	        fig = plt.figure('ASIC {}'.format(asic), (20.,8.))
	        fig.suptitle("Asic {}".format(asic), fontsize=16, fontweight='bold', bbox={'boxstyle':'round4','facecolor':'gray', 'alpha':0.5})
	        gs = gridspec.GridSpec(4,4)
	        gs.update(left=0.06,right= 0.98, top=0.93, bottom = 0.05, wspace=0.25,hspace=0.25)
	
	        for channel in range(nchannel):
	
	            ax1 = plt.subplot(gs[channel/4, channel%4])
	            ax1.set_xlabel('ns')
	            ax1.set_ylabel('raw ADC counts')
	            ax1.grid(True)
	            plt.text(0.65, 0.9," Channel {}".format(channel), transform = ax1.transAxes, bbox={'boxstyle':'roundtooth','facecolor':'grey', 'alpha':0.2})

	            for ievt in range(0,nEvents):
			
	                rawdata = reader.GetEventPacket(ievt,asic*(nchannel/chPerPacket)+(channel/chPerPacket))
	                packet = target_driver.DataPacket()
        	        packet.Assign(rawdata, reader.GetPacketSize())
			header = target_driver.EventHeader()
			reader.GetEventHeader(ievt, header);
			sec = 0
			nanosec = 0
			#header.GetTimeStamp(&sec, &nanosec)
			#print "Tack message: ", header.GetTACK(), "Filled packets: ", header.GetNPacketsFilled(), "Timestamp: ", sec, nanosec
        	       # wf = packet.GetWaveform(channel%8)
        	        wf = packet.GetWaveform(channel%chPerPacket)
			#if(ievt==0): print "Number of samples: ", wf.GetSamples()
        	        #print asic, wf.GetASIC()
        	        #print channel, wf.GetChannel()
        	        for sample in range(nSamples):
        	            ampl[ievt,asic, channel, sample] = wf.GetADC(sample)
        	        #if np.any(ampl == 0):
        	        #    print np.where(ampl == 0)
			blockNumber=(packet.GetRow()*64 + packet.GetColumn())
			blockPhase=(packet.GetBlockPhase() )
			if(0): print "blockNumber", blockNumber, "blockPhase", blockPhase
#			if(blockNumber==180 and blockPhase/8==0 ):
        	        ax1.plot(ampl[ievt, asic, channel], alpha=0.3, linewidth = 0.5)
#			ax1.set_ylim(550,1200)

       		#fig.savefig(basename+"_ADCwfAsic{}.pdf".format(asic))
		saveDir = "%s/Pictures/%s" % (homedir, outdirname) 
		try:
			os.mkdir(saveDir)
		except:
			print "Directory couldn't be created."	
        	fig.savefig('%s/run%dASIC%dw%dEvent.png' % (saveDir, runID, asic, nEvents))


#plt.show()
