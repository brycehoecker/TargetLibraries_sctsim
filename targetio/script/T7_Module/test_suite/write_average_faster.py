import target_io
import target_driver
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec
import sys
import time

startTime = time.time()

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

for i in range(start,stop+1):
   runN = i

   channelsPerPacket=1	
   filename = "/Users/mileswinter/target5and7data/run"+str(runN)+".fits"
   nBlocks = 8
   nSamples = nBlocks*32
   nPhases = 4
   for Nasic in range(1):
	for Nchannel in range(14,15):

		reader = target_io.EventFileReader(filename)
		nEvents = reader.GetNEvents()
		print "Run:", runN, " Channel:",Nchannel, " Asic:",Nasic," number of events", nEvents
	
		offset=0	
		nEvents = reader.GetNEvents()
		print "number of events", nEvents
		limit=1000000
		startEvents=0
		if(nEvents>limit):
			print "Plot only first %d events!" % limit
			nEvents=limit
	 
		meanAmpl = np.zeros([512,nPhases,nSamples])
		meanCount = np.zeros([512,nPhases])
	    	count=0
	        packet = target_driver.DataPacket()
	        for ievt in range(startEvents,nEvents):
			if(ievt%1000==0):
				sys.stdout.write('\r')
				sys.stdout.write("[%-100s] %d%%" % ('='*int((ievt-startEvents)*100.0/(nEvents-startEvents)) , (ievt-startEvents)*100.0/(nEvents-startEvents)))
				sys.stdout.flush()

                        
                        rawdata = reader.GetEventPacket(ievt,Nasic*16/channelsPerPacket+Nchannel/channelsPerPacket)
	                #rawdata = reader.GetEventPacket(ievt,Nasic*16+Nchannel)
	                packet.Assign(rawdata, reader.GetPacketSize())
			#blockNumber=(packet.GetRow()*64 + packet.GetColumn())
                        blockNumber = (packet.GetColumn()*8+packet.GetRow())
			blockPhase=packet.GetBlockPhase()
			offset = blockPhase - int(int(blockPhase)/8)*8
                        wf = packet.GetWaveform(Nchannel%channelsPerPacket)
	                #wf = packet.GetWaveform(0)
			meanCount[blockNumber,(blockPhase-offset)/8]+=1
                        #meanCount[blockNumber,blockPhase]+=1
		        for sample in range(nSamples):
		        	meanAmpl[blockNumber,(blockPhase-offset)/8,sample]+=wf.GetADC(sample)
                                #meanAmpl[blockNumber,blockPhase,sample]+=wf.GetADC(sample)
		sys.stdout.write('\n')
                
                #create output file and temp array to store average waveforms
                outfile = "runFiles/flasher_av_run"+str(runN)+"ASIC"+str(Nasic)+"CH"+str(Nchannel)+".npz"
                run = np.ones(512*nPhases,dtype=int)*runN
                asic = np.ones(512*nPhases,dtype=int)*Nasic
                channel = np.ones(512*nPhases,dtype=int)*Nchannel
                block = np.zeros(512*nPhases,dtype=int)
                phase = np.zeros(512*nPhases,dtype=int)
                baseline = np.zeros((512*nPhases,nSamples),dtype=int)

		for bn in range(512):
			for bp in range(nPhases):
				Nphase = bp*8+4
                                index = bn*nPhases+bp
                                block[index] = bn
                                phase[index] = Nphase
				for sample in range(nSamples):
					if(meanCount[bn,bp]>0):
						baseline[index,sample] = meanAmpl[bn,bp, sample]*1.0/meanCount[bn,bp]

                #store data with associated keywords
                #######################################################################
                #LOADING DATA: use np.load('path/filename.npz')                       #
                #List of keywords: run, asic, channel, block, phase, baseline         #
                #EXAMPLE: my_data = np.load('path/filename.npz')                      #
                #Now call keyword: phase = my_data['phase']                           #
                #######################################################################
                np.savez_compressed(outfile,run=run, asic=asic, channel=channel, block=block, phase=phase, baseline=baseline)
					
                sys.stdout.write('\n')	

endTime = time.time()
print "This took", endTime- startTime, "seconds."
