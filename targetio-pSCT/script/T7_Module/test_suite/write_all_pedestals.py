#------------------------------------------------------------------------#
#  Author: Miles Winter                                                  #
#  Date: 08-25-2017                                                      #
#  Project: CTA                                                          #
#  Desc: Calculate average pedestal waveforms from calibration           #
#        data and create a .h5 database for storage                      #
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

#specify output directory for pedestal database
outdir = os.environ['HOME']+'/test_suite/runFiles/'

#number of phases
nPhases = 32


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

    #specify output name for pedestal database
    outfile = outdir+'pedestal_database_run{}.h5'.format(run_num)

    #Check if filename already exists
    if os.path.isfile(outfile)==True:
	print 'The file {} already exists!'.format(outfile)
	answers = {"yes","no"}
	choice = ''
	while True:
	    choice = raw_input("Would you like to overwrite it? (yes/no) ")
	    if choice in answers:
		break
	    else:
		print "Not an acceptable input, try again {}!".format(pwd.getpwuid(os.getuid()).pw_name)
	if choice == 'no':
	    print 'EXITING'
	    raise SystemExit

    #create database for each run
    print 'Creating pedestal database from run {}'.format(run_num)
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

		print "Calculating pedestals for Module {}, Run {}, Asic {}, Channel {}".format(Nmod, run_num,Nasic, Nchannel)
  
                #create arrays to hold pedestals
                avg_pedestal = np.zeros((512,nPhases,nSamples))
                counts = np.zeros((512,nPhases))                

	        for ievt in xrange(nEvents):
		    rawdata = reader.GetEventPacket(ievt,(4*modInd+Nasic)*16/channelsPerPacket+Nchannel/channelsPerPacket)
		    packet = target_driver.DataPacket()
		    packet.Assign(rawdata, reader.GetPacketSize())
		    block = int(packet.GetColumn()*8+packet.GetRow())
		    phase = int(packet.GetBlockPhase())
		    wf = packet.GetWaveform(Nchannel%channelsPerPacket)
                    samples = np.zeros(nSamples)
                    #get all samples
		    for sample in xrange(nSamples):
			    samples[sample] = int(wf.GetADC(sample))

                    #reject events with data spikes
                    if np.amin(samples)>100.: 
                        avg_pedestal[block,phase,:] += samples[:]
                        counts[block,phase] += 1.

                #Create database branch and add data for each block and phase
		for b in xrange(512):
		    for p in xrange(nPhases):
			if counts[b,p]>0.:
			    ped_waveform = np.round(avg_pedestal[b,p,:]/counts[b,p],decimals=2)
                            branch_name = "Module{}/Asic{}/Channel{}/Block{}/Phase{}".format(Nmod,Nasic,Nchannel,b,p)
                            branch = f.create_group(branch_name)
                            branch.create_dataset("pedestal", data=ped_waveform)
                             


    f.close()
    print "Run Completed: database saved to {}".format(outfile)	
