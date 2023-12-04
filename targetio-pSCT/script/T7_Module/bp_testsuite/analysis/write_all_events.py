#------------------------------------------------------------------------#
#  Author: Miles Winter                                                  #
#  Date: 08-25-2017                                                      #
#  Project: CTA                                                          #
#  Desc: Convert data from .fits to .h5                                  #
#  Note: Need h5py installed: pip install --upgrade h5py                 #
#        Documentation at http://www.h5py.org/                           #
#------------------------------------------------------------------------#


import target_io
import target_driver
import numpy as np
import sys, os
import time
import h5py

argList = sys.argv

if(len(argList)>2):
    start = int(argList[1])
    stop = int(argList[2])
elif(len(argList)>1):
    start = int(argList[1])
    stop = start
else:
    print 'Incorrect usage: No run number(s) specified'
    print 'Correct usage: python {} 123456'.format(argList[0])
    print 'EXITING'
    raise SystemExit

#define list of run numbers
run_list = np.arange(start,stop+1,1)

#define list of module numbers (must be same order as when data was taken)
modList=[118 ,125, 126, 101, 119, 108, 116, 110, 128, 123, 124, 112, 100, 111, 114, 107]

#specify output directory
outdir = os.environ['HOME']+'/runFiles/'


#------------------------------------------------------------------------#

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

    #create database for each run
    print 'Creating database for run {}'.format(run_num)
    outfile = outdir+'run{}.h5'.format(run_num)
    f = h5py.File(outfile,"w")

    #loop through each module
    for modInd, Nmod in enumerate(modList):
        #loop through each asic
        for Nasic in xrange(4):
            #loop through each channel
	    for Nchannel in xrange(16):
                
                #Determine number of events and samples in the waveforms:
		reader = target_io.EventFileReader(filename)    
		nEvents = reader.GetNEvents()
	        rawdata = reader.GetEventPacket(0,0)
	        packet = target_driver.DataPacket()
                PacketSize = reader.GetPacketSize()
                packet.Assign(rawdata, PacketSize)
                wf = packet.GetWaveform(0)
                nSamples = wf.GetSamples()
                channelsPerPacket = GetChannelsPerPacket(PacketSize, nSamples)

		print "Writing events for Module {}, Run {}, Asic {}, Channel {}".format(Nmod, run_num,Nasic, Nchannel)
  
                #create arrays to hold samples
                run = np.array([run_num],dtype=int)
                module = np.array([Nmod],dtype=int)
                asic = np.array([Nasic],dtype=int)
                channel = np.array([Nchannel],dtype=int)
                event = np.zeros(nEvents,dtype=int)
                block = np.zeros(nEvents,dtype=int)
                phase = np.zeros(nEvents,dtype=int)
                samples = np.zeros((nEvents,nSamples),dtype=int)

	        for ievt in xrange(nEvents):
		    rawdata = reader.GetEventPacket(ievt,(4*modInd+Nasic)*16/channelsPerPacket+Nchannel/channelsPerPacket)
		    packet = target_driver.DataPacket()
		    packet.Assign(rawdata, reader.GetPacketSize())
		    blockNumber = (packet.GetColumn()*8+packet.GetRow())
		    blockPhase=(packet.GetBlockPhase())
		    wf = packet.GetWaveform(Nchannel%channelsPerPacket)
		    event[ievt] = int(ievt)
		    block[ievt] = int(blockNumber)
		    phase[ievt] = int(blockPhase)
		    for sample in xrange(nSamples):
			    samples[ievt,sample] = int(wf.GetADC(sample))

                #Create database branch and add data
                branch_name = "Module{}/Asic{}/Channel{}".format(Nmod,Nasic,Nchannel)
                branch = f.create_group(branch_name)
                branch.create_dataset("module", data=module)
                branch.create_dataset("run", data=run)
                branch.create_dataset("asic", data=asic)
                branch.create_dataset("channel", data=channel)
                branch.create_dataset("event", data=event)
                branch.create_dataset("block", data=block)
                branch.create_dataset("phase", data=phase)
                branch.create_dataset("samples", data=samples)                             


    f.close()
    print "Run Completed: database saved to {}".format(outfile)	
