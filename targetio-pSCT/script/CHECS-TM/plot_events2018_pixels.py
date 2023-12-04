import target_driver
import target_io
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
import numpy as np
import pdb
import scipy.optimize as opt
import scipy
import reportlab
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from scipy.signal import butter, lfilter, freqz
from astropy.io import ascii


def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y


filename_raw = "/media/cta/157bfe11-9587-4947-8a3e-1e814c5c25dc/Messungen_Stefan/Raw/file_9_r0.tio"
filename_cal = "/media/cta/157bfe11-9587-4947-8a3e-1e814c5c25dc/Messungen_Stefan/Raw/file_9_r1.tio"

Nsamples = 8*32
SCALE=13.6
OFFSET=700

plotchan = 0
nevt = 20
reader_raw = target_io.EventFileReader(filename_raw)
reader_cal = target_io.EventFileReader(filename_cal)
NEvents  = reader_raw.GetNEvents()

print(NEvents, "events read")

ampl_raw = np.zeros([64,nevt,200])
ampl_cal = np.zeros([64,nevt,200])






#ax2[0].set_title("raw ADC counts",fontsize=10)
#ax2[1].set_title("pedestal substracted ADC counts", fontsize=10)

#ax_cal =plt.subplot(211)
#ax_cal.set_xlabel("sample",fontsize=14)
#ax_cal.set_ylabel("pedestal substracted ADC counts", fontsize=14)
#ax_cal.set_title("Channel "+str(channel))



timestamp=0
timestamp_prev=0

if nevt==0:
    nevt=NEvents



for ievt in range(0,nevt,1):
	event_head = target_driver.EventHeader()
	ret=reader_raw.GetEventHeader(ievt,event_head)
	#get timestamp in ns from event header
	timestamp=event_head.GetTACK()
	print("\nEvent ",ievt, " Timestamp in ns",timestamp, " Time since last Event in us ",(timestamp-timestamp_prev)/1000.)
	timestamp_prev=timestamp
	#first get the right packet from event, if only one channel/packet, then packetnumber = channel
	for group in range (0,16):
	    rawdata_raw = reader_raw.GetEventPacket(ievt,int(group))
	    rawdata_cal = reader_cal.GetEventPacket(ievt,int(group))
	    packet_raw = target_driver.DataPacket()
	    packet_cal = target_driver.DataPacket()
	    packet_raw.Assign(rawdata_raw, reader_raw.GetPacketSize())
	    packet_cal.Assign(rawdata_cal, reader_cal.GetPacketSize())
	    if group == 0:
	    	print("Starting Block: Col",packet_raw.GetColumn(),"Row",packet_raw.GetColumn(),"Phase",packet_raw.GetBlockPhase())
	    for gchannel in range(0,4):
		    #get the waveform, if only one channel/packet, only one waveform!
		    wf_raw = packet_raw.GetWaveform(int(gchannel))
		    wf_cal = packet_cal.GetWaveform(int(gchannel))
		    ampl_raw[group*4+gchannel][ievt]=wf_raw.GetADCArray(200)
		    ampl_cal[group*4+gchannel][ievt]=((wf_cal.GetADC16bitArray(200))/SCALE)-OFFSET
   


# Filter requirements.
order = 5
fs = 1.0e9       # sample rate, Hz
cutoff = 100.0e6  # desired cutoff frequency of the filter, Hz

# Get the filter coefficients so we can check its frequency response.
b, a = butter_lowpass(cutoff, fs, order)

# Filter the data, and plot both the original and filtered signals.
y = butter_lowpass_filter(ampl_cal, cutoff, fs, order)


#print (np.amax(y, axis=2))
#print (np.argmax(y, axis=2))

meanwave=np.mean(y,axis=0)

#print (meanwave[19])

#exit()

maxval=np.amax(y, axis=2)
maxpos=np.argmax(y, axis=2)



xulim = 200
xllim = 0
yulim = 50
yllim = -10


data = ascii.read("/home/cta/Software/TargetIO/trunk/script/CHECS-TM/pixel_arrangement.txt")

#print(maxval[:,1])

#print(np.mean(maxval,axis=1))


t=np.mean(maxval,axis=1)

x=data[1][:]
y=data[2][:]

hb = plt.hexbin(x, y,maxpos[:,14],  gridsize=8, cmap='inferno')
plt.axis([-5, 55, -5, 40])
plt.axis('off')
plt.show()



#for channel in range (0,64):
    



#ax=[]
#axx=[]
#axy=[]


#for channel in range (0,64):
    
    ##ax[channel].set_xlim([xllim, xulim])
    ##ax[channel].set_ylim([yllim, yulim])
    #for event in range (0,1):
        #print ampl_cal[channel,event])
        

           #axx.append(data[channel][1])
           #axy.append(data[channel][2])

#plt.plot(axx[], axy[])

#hb = ax.hexbin(x, y, gridsize=2, cmap='inferno')
#ax.axis([xmin, xmax, ymin, ymax])
#ax.set_title("Counts/Pixel")
#cb = fig.colorbar(hb, ax=ax)
#cb.set_label('counts')



#plt.show()