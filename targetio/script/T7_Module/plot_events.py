import target_io
import target_driver
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec
import datetime
import time
import scipy.io

now = datetime.datetime.now()
outdirname = now.strftime("%m%d%y")

applyCalibration = 1

# TF info, only used when applyCalibration
tfMinRun = 297586
tfMaxRun = 297610
tfNumEvent = 500

runList = range(297590,297590+1)
numBlock = 2
nSamples = 32*numBlock
nchannel = 16
nasic = 4


for runID in runList:

	filename = "/Users/twu58/target5and7data/run%d.fits" % (runID)
	reader = target_io.EventFileReader(filename)
	nEvents = reader.GetNEvents()
	print "number of events", nEvents

	ampl = np.zeros([nEvents,nasic, nchannel, nSamples])
	for asic in range(nasic):
	#for asic in range(1):
	        fig = plt.figure('ASIC {}'.format(asic), (20.,8.))
	        fig.suptitle("Asic {}".format(asic), fontsize=16, fontweight='bold', bbox={'boxstyle':'round4','facecolor':'gray', 'alpha':0.5})
	        gs = gridspec.GridSpec(4,4)
	        gs.update(left=0.06,right= 0.98, top=0.93, bottom = 0.05, wspace=0.25,hspace=0.25)
	
	        for channel in range(nchannel):

		    if applyCalibration:
		    	if channel >= 10:
                        	tffilename = "/Users/twu58/targetTF/target7TF_chan%d_runs%dto%d_%devents_25points_direct_offset0_clean0.mat" % (channel,tfMinRun,tfMaxRun,tfNumEvent)
                    	else:
                        	tffilename = "/Users/twu58/targetTF/target7TF_chan0%d_runs%dto%d_%devents_25points_direct_offset0_clean0.mat" % (channel,tfMinRun,tfMaxRun,tfNumEvent)

                    	mat = scipy.io.loadmat(tffilename)

	
	            ax1 = plt.subplot(gs[channel/4, channel%4])
	            ax1.set_xlabel('ns')
		    if applyCalibration:
		    	ax1.set_ylabel('DC voltage (V)')
		    else:
	            	ax1.set_ylabel('raw ADC counts')
	            ax1.grid(True)
	            plt.text(0.65, 0.9," Channel {}".format(channel), transform = ax1.transAxes, bbox={'boxstyle':'roundtooth','facecolor':'grey', 'alpha':0.2})

		    ##starttime = time.time()

	            for ievt in range(nEvents):
	                rawdata = reader.GetEventPacket(ievt,asic*nchannel+channel)
	                packet = target_driver.DataPacket()
        	        packet.Assign(rawdata, reader.GetPacketSize())
        	        wf = packet.GetWaveform(0)
        	        #print asic, wf.GetASIC()
        	        #print channel, wf.GetChannel()
        	        for sample in range(nSamples):
			    if applyCalibration:
			    	ampl[ievt,asic,channel,sample] = mat.get('invertedTFs')[sample,wf.GetADC(sample)]
			    else:
        	            	ampl[ievt,asic, channel, sample] = wf.GetADC(sample)
        	        #if np.any(ampl == 0):
        	        #    print np.where(ampl == 0)

        	        ax1.plot(ampl[ievt, asic, channel],alpha=1, linewidth = 0.1)
		    ##endtime = time.time()
		    ##print endtime-starttime
		    ##time.sleep(100)

       		#fig.savefig(basename+"_ADCwfAsic{}.pdf".format(asic))
		if applyCalibration:
        		fig.savefig('/Users/twu58/Pictures/%s/run%dASIC%dw%dEventC.png' % (outdirname, runID, asic, nEvents))
		else:
			fig.savefig('/Users/twu58/Pictures/%s/run%dASIC%dw%dEvent.png' % (outdirname, runID, asic, nEvents))

#plt.show()
