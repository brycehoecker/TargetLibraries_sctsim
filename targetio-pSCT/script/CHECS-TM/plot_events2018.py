import target_driver
import target_io
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pdb
#import plotly.plotly as py


filename_raw = "file_0_r0.tio"
filename_cal = "file_0_r1.tio"

Nsamples = 4*32
SCALE=13.6
OFFSET=700

plotchan = 0

reader_raw = target_io.EventFileReader(filename_raw)
reader_cal = target_io.EventFileReader(filename_cal)
NEvents  = reader_raw.GetNEvents()

print(NEvents, "events read")

ampl_raw = np.zeros([64,NEvents,Nsamples])
ampl_cal = np.zeros([64,NEvents,Nsamples])
#f, ax2 = plt.subplots(2, sharex=True)

#f,ax2 = plt.subplots(8,8)




#ax2[0].set_title("raw ADC counts",fontsize=10)
#ax2[1].set_title("pedestal substracted ADC counts", fontsize=10)

#ax_cal =plt.subplot(211)
#ax_cal.set_xlabel("sample",fontsize=14)
#ax_cal.set_ylabel("pedestal substracted ADC counts", fontsize=14)
#ax_cal.set_title("Channel "+str(channel))

nevt = 0

timestamp=0
timestamp_prev=0

if nevt==0:
    nevt=NEvents
    
badseries = False
badtimestamps = []

for ievt in range(0,nevt,1):
	event_head = target_driver.EventHeader()
	ret=reader_raw.GetEventHeader(ievt,event_head)
	#get timestamp in ns from event header
	timestamp=event_head.GetTACK()
	delay = (timestamp-timestamp_prev)/1000.
	if (ievt%1000==0):
	    print("\nEvent ",ievt, " Timestamp in ns",timestamp, " Time since last Event in us ",(timestamp-timestamp_prev)/1000.)
	timestamp_prev=timestamp
	#first get the right packet from event, if only one channel/packet, then packetnumber = channel
	for group in range (1,2):
	    rawdata_raw = reader_raw.GetEventPacket(ievt,int(group))
	    rawdata_cal = reader_cal.GetEventPacket(ievt,int(group))
	    packet_raw = target_driver.DataPacket()
	    packet_cal = target_driver.DataPacket()
	    packet_raw.Assign(rawdata_raw, reader_raw.GetPacketSize())
	    packet_cal.Assign(rawdata_cal, reader_cal.GetPacketSize())
	    if group == 0:
	    	print("Starting Block: Col",packet_raw.GetColumn(),"Row",packet_raw.GetColumn(),"Phase",packet_raw.GetBlockPhase())
	    for gchannel in range(3,4):
		    #get the waveform, if only one channel/packet, only one waveform!
		    wf_raw = packet_raw.GetWaveform(int(gchannel))
		    wf_cal = packet_cal.GetWaveform(int(gchannel))
		    ampl_raw[group*4+gchannel][ievt]=wf_raw.GetADCArray(Nsamples)
		    ampl_cal[group*4+gchannel][ievt]=((wf_cal.GetADC16bitArray(Nsamples))/SCALE)-OFFSET
		    if np.max(ampl_cal[group*4+gchannel][ievt])>35:
		        if (badseries == False):
		            print("bad event ",ievt,"for delay",delay)
		        badseries=True
		        badtimestamps.append(delay)
		        #plt.plot(((wf_cal.GetADC16bitArray(Nsamples))/SCALE)-OFFSET)
		    else :
		        badseries = False
        
    
	#ax2[0].plot(ampl_raw[plotchan][ievt],alpha=0.7)
	#ax2[1].plot(ampl_cal[plotchan][ievt],alpha=0.7)
	#ax2[0].set_xlim([0, 200])
	#ax2[1].set_ylim([-10, 10])
	
	#for i in range (0,64):
	#	ax2[i%8,int(i/8)].set_xlim([0, 200])
	#	ax2[i%8,int(i/8)].set_ylim([-10, 50])
	#	ax2[i%8,int(i/8)].plot(ampl_cal[i][ievt],alpha=0.7)


plt.hist(badtimestamps,bins=1000)





plt.show()



