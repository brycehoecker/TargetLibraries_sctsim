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


def plot_events(runList, testDir, dataset, group=0, numBlock=2):
	now = datetime.datetime.now()
	outdirname = now.strftime("%m%d%y")

	for runID in runList:

		homedir = os.environ['HOME']
		hostname = run_control.getHostName()
		outdirname = run_control.getDataDirname(hostname)
		indirname = testDir
		filename = outdirname+"/run{}.fits".format(runID)

		nSamples = numBlock*32
		nchannel = 16
		nasic = 4
	
		reader = target_io.EventFileReader(filename)
		nEvents = reader.GetNEvents()
		print "number of events", nEvents
		nEventsOut = nEvents
		if(nEvents>300):
			print "Plot only first 300 events!"
			nEvents=300
	
		ampl = np.zeros([nEvents,nasic, nchannel, nSamples])
		for asic in range(nasic):
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
	
		            for ievt in range(nEvents):
		                rawdata = reader.GetEventPacket(ievt,asic*nchannel+channel)
		                packet = target_driver.DataPacket()
	        	        packet.Assign(rawdata, reader.GetPacketSize())
	        	        wf = packet.GetWaveform(0)
	        	        #print asic, wf.GetASIC()
	        	        #print channel, wf.GetChannel()
	        	        for sample in range(nSamples):
	        	            ampl[ievt,asic, channel, sample] = wf.GetADC(sample)
	        	        #if np.any(ampl == 0):
	        	        #    print np.where(ampl == 0)
	        	        ax1.plot(ampl[ievt, asic, channel], alpha=1, linewidth = 0.5)
	
	       		#fig.savefig(basename+"_ADCwfAsic{}.pdf".format(asic))
			saveDir = testDir 
	        	fig.savefig('{}/run{}ASIC{}_{}Events_gr{}_{}.png'.format(saveDir, runID, asic, nEventsOut, group,dataset ) )


