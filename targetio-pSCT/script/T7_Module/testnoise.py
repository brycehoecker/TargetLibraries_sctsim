import target_io
import target_driver
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec
import time
import datetime

now = datetime.datetime.now()
outdirname = now.strftime("%m%d%y")

#runIDList = [286186]

#ModuleList = [107]

#runIDList = range(288141,288145+1)

#runIDList = [288517,288505,288513]

#runIDList = [288515,288503,288531,288529]

#runIDList = range(289164,289165+1)

#runIDList = [289156,289174,289158,289146,289186,289192,289172,289166,289164]

#runIDList = [290792,290793,290794,290795]

runIDList = range(292069,292069+1)

#runIDList = range(290033,290034+1)

#runIDList = [288814,289146,289147,290035,290036]

#filename = "/Users/twu58/target5and7data/run%d.fits" % (runID)
#filename = "/Users/pkarn/T7Module/data/20160209/test_dump40.fits"
nSamples = 32*14
nchannel = 16
nasic = 4

for runID in runIDList:

        filename = "/Users/twu58/target5and7data/run%d.fits" % (runID)
	reader = target_io.EventFileReader(filename)
	nEvents = reader.GetNEvents()

        SigmaList = []
        MaxList = []
        MinList = []

        for asic in range(nasic):

                for channel in range(nchannel):

                        sigmal = []
                        ampll = []

                        for ievt in range(nEvents):
				ampl = np.zeros([nSamples])

				rawdata = reader.GetEventPacket(ievt,asic*nchannel+channel)
				packet = target_driver.DataPacket()
				packet.Assign(rawdata, reader.GetPacketSize())
				wf = packet.GetWaveform(0)
				for sample in range(nSamples):
					ampl[sample] = (wf.GetADC(sample))					
				#print(ampl)
				#time.sleep(100)
				sigmal.append(np.std(ampl))
				ampll.append(ampl)
				del ampl

			am = np.concatenate(ampll)

			del sigmal
			sigmal = []

			for icell in range(nSamples):
				amplll = []
                                for iievt in range(nEvents):
                                        #if(am[iievt*nSamples+icell]>700.0):amplll.append(am[iievt*nSamples+icell])
					amplll.append(am[iievt*nSamples+icell])
                                sigmal.append(np.std(amplll))

                                del amplll

                        SigmaList.append(np.mean(sigmal))
                        MaxList.append(max(sigmal))
                        MinList.append(min(sigmal))

                        del sigmal
                        del ampll
                        del am

        fig = plt.plot(range(64),SigmaList)
        #fig2 = plt.plot(range(64),MaxList)
        #fig3 = plt.plot(range(64),MinList)
        #plt.title("Noise plot (uncalibrated) Module %d" % (ModuleList[0]))
        #plt.title("Noise plot with modified or unmodified cables Module %d" % (ModuleList[0]))
	plt.title("Noise plot with HV on M111 4,1i0")
        plt.xlabel('Channel Number (ASIC number*16+channel number)')
        plt.ylabel('Noise (ADC Counts)')
	#plt.legend(['M Cable 1','M Cable 2','Unm Cable 1','Unm Cable 2'],loc=0)
	##plt.legend(['FEE 111 FPM 4,1','FEE 111 FPM 4,7','FEE 111 FPM 4,10','FEE 123 FPM 4,1','FEE 123 FPM 4,7','FEE 123 FPM 4,10','FEE 128 FPM 4,1','FEE 128 FPM 4,7','FEE 128 FPM 4,10'],loc=0,fontsize=12)
	#plt.legend(['FEE','FPM','FPM new','FEE new'],loc=0)
        #plt.legend(['mean noise all cables mod.','no shield at module ASIC2'],loc=0)
        #plt.legend(['0','10','20','30','40','50','60','70','80','90','100'])
	#plt.legend(['0','30','60','90','120','150','180','210','240','270','300'])
        #plt.legend(['unmod. cable','mod. cable at module','mod cable at focal plane','ASIC2 grounded at focal plane','ASIC2 grounded at module','mod. cable at module, verification'],loc=0)
	##plt.legend(['M2','M1','G2','G1','G2(ASIC3)'],loc=0)
        #plt.savefig('/Users/twu58/Pictures/%s/run%d_%dEventNoiseM%d.png' % (outdirname, runID, nEvents, ModuleList[0]))
	plt.savefig('/Users/twu58/Pictures/%s/run%d_%dEventNoise.png' % (outdirname, runID, nEvents))
        #del ModuleList[0]
#        plt.clf()
#        plt.show()


