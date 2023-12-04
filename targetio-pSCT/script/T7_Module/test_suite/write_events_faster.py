import target_io
import target_driver
import numpy as np
import sys, os
import time

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

#define list of run numbers
run_list = np.arange(start,stop+1,1)

def GetChannelsPerPacket(PacketSize, nSamples):
    cpp = (0.5*PacketSize-10.)/(nSamples+1.)
    return int(cpp)

#Check if remote data directory is mounted
if os.path.ismount(os.environ['HOME']+'/target5and7data')==True:
    print "Output-directory is mounted"
else:
    print "Cannot connect to the remote output directory!"
    print 'Make sure ',os.environ['HOME']+'/target5and7data',' is mounted!'
    print 'EXITING'
    raise SystemExit

print 'Locating data for run(s) {}'.format(run_list)

#loop through each run
for run_num in run_list:
    filename = "{}/target5and7data/run{}.fits".format(os.environ['HOME'],run_num)

    #Check if input .fits file exists
    if os.path.isfile(filename)==True:
        print "Data file located: {}".format(filename)
    else:
        new_path = "{0}/target5and7data/runs_{1}0000_through_{1}9999/".format(os.environ['HOME'],str(run_num)[:-4])
        filename = new_path+"run{}.fits".format(run_num)
        if os.path.isfile(filename)==True:
            print "Data file located: {}".format(filename)
        else:
            print "File run{}.fits cannot be located. Verify run number".format(run_num)
            print 'EXITING'
            raise SystemExit

    for Nasic in range(33,34):
	for Nchannel in range(13,14):
        #for Nchannel in range(2,3):
                
                startTime = time.time()

		reader = target_io.EventFileReader(filename)
		nEvents = reader.GetNEvents()
		#Do this once, so we can determine the number of samples in the waveform:
	        rawdata = reader.GetEventPacket(0,0)
	        packet = target_driver.DataPacket()
                PacketSize = reader.GetPacketSize()
	        packet.Assign(rawdata, PacketSize)
	        wf = packet.GetWaveform(0)
		nSamples = wf.GetSamples()
                channelsPerPacket = GetChannelsPerPacket(PacketSize,nSamples)

		print "Writing Events For Run:", run_num, " Asic: ",Nasic," Channel: ",Nchannel
                print "Number of events: ", nEvents, ", Length of the waveform: ", nSamples

		limit=2000000
		startEvents=0
		if(nEvents>limit):
			print "Plot only first %d events!" % limit
			nEvents=limit
  

                #name output file and create array to hold samples
                outfile = "runFiles/sampleFileAllBlocks_run"+str(run_num)+"ASIC"+str(Nasic)+"CH"+str(Nchannel)+".npz"
                run = np.ones(nEvents,dtype=int)*run_num
                asic = np.ones(nEvents,dtype=int)*Nasic
                channel = np.ones(nEvents,dtype=int)*Nchannel
                event = np.zeros(nEvents,dtype=int)
                block = np.zeros(nEvents,dtype=int)
                phase = np.zeros(nEvents,dtype=int)
                timestamp = np.zeros(nEvents,dtype=int)
                samples = np.zeros((nEvents,nSamples),dtype=int)
	        for ievt in range(startEvents,nEvents):
			if(ievt%100==0):
				sys.stdout.write('\r')
				sys.stdout.write("[%-100s] %.1f%%" % ('='*int((ievt-startEvents)*100.0/(nEvents-startEvents)) , (ievt-startEvents)*100.0/(nEvents-startEvents)))
				sys.stdout.flush()
	                rawdata = reader.GetEventPacket(ievt,Nasic*16/channelsPerPacket+Nchannel/channelsPerPacket)
                        packet = target_driver.DataPacket()
	                packet.Assign(rawdata, reader.GetPacketSize())
                        blockNumber = (packet.GetColumn()*8+packet.GetRow())
			blockPhase=(packet.GetBlockPhase() )
	                wf = packet.GetWaveform(Nchannel%channelsPerPacket)
                        event[ievt] = int(ievt)
                        block[ievt] = int(blockNumber)
                        phase[ievt] = int(blockPhase)
                        timestamp[ievt] = packet.GetTACKTime()
                        packetID = packet.GetPacketID()
			if not packetID[0]:
			    samples[ievt,:] = -1
			else:
			    for sample in xrange(nSamples):
				    samples[ievt,sample] = int(wf.GetADC(sample))
               
                #store data with associated keywords
                #######################################################################
                #LOADING DATA: use np.load('path/filename.npz')                       #
                #List of keywords: run, asic, channel, event, block, phase, samples   #
                #EXAMPLE: my_data = np.load('path/filename.npz')                      #
                #Now call keyword: phase = my_data['phase']                           #
                #######################################################################
                np.savez_compressed(outfile,run=run, asic=asic, channel=channel, event=event, block=block, phase=phase, timestamp=timestamp, samples=samples)

                sys.stdout.write('\n')
                print "Writing Complete: Saving to",outfile
                print "Job Time: ", time.time()- startTime, "seconds."
                sys.stdout.write('\n')
	
