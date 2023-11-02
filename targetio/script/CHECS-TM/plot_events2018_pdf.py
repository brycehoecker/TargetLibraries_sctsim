import image
import target_io
import target_driver
#import cStringIO
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pdb
from scipy.signal import butter, lfilter, freqz
import scipy
#import reportlab
#from reportlab.pdfgen import canvas
#from reportlab.lib.units import cm
#from reportlab.lib.pagesizes import landscape
#from reportlab.lib.utils import ImageReader

#import plotly.plotly as py


def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y


#filename_raw = "/DATA/Messungen_Stefan/Raw/file_0_r0.tio"
filename_cal = "/DATA/Messungen_Stefan/Raw/file_650_UHG_r1.tio"
#filename_cal = "/DATA/Messungen_Stefan/003_pulsed_laser/Tune 60/file_0_r1_60.tio"
#filename_cal = "/DATA/Messungen_Stefan/Raw/pedestal_r1.tio"
Nsamples = 8*32
SCALE=13.6
OFFSET=700

plotchan = 0

#reader_raw = target_io.EventFileReader(filename_raw)
reader_cal = target_io.EventFileReader(filename_cal)
NEvents  = reader_cal.GetNEvents()

print(NEvents, "events read")


nevt = 100000

#ampl_raw = np.zeros([64,nevt,Nsamples])
ampl_cal = np.zeros([64,nevt,Nsamples])
firstsample = np.zeros(nevt)




timestamp=0
timestamp_prev=0

if nevt==0:
    nevt=NEvents



for ievt in range(0,nevt,1):
	event_head = target_driver.EventHeader()
	ret=reader_cal.GetEventHeader(ievt,event_head)
	if (ievt%5000==0):
            print('Event {} of {}'.format(ievt,nevt))
	#get timestamp in ns from event header
	timestamp=event_head.GetTACK()
	#print("\nEvent ",ievt, " Timestamp in ns",timestamp, " Time since last Event in us ",(timestamp-timestamp_prev)/1000.)
	timestamp_prev=timestamp
	#first get the right packet from event, if only one channel/packet, then packetnumber = channel
	for group in range (0,16):
	    #rawdata_raw = reader_raw.GetEventPacket(ievt,int(group))
	    rawdata_cal = reader_cal.GetEventPacket(ievt,int(group))
	    #packet_raw = target_driver.DataPacket()
	    packet_cal = target_driver.DataPacket()
	    #packet_raw.Assign(rawdata_raw, reader_raw.GetPacketSize())
	    packet_cal.Assign(rawdata_cal, reader_cal.GetPacketSize())	    
	    if group == 0:
                firstsample[ievt]=(packet_cal.GetRow())*32+(packet_cal.GetColumn())*8*32+(packet_cal.GetBlockPhase())
                #if (packet_cal.GetBlockPhase() != 31 and packet_cal.GetBlockPhase() != 0):
                        #print("Event",ievt, "Starting Block: Col",packet_cal.GetColumn(),"Row",packet_cal.GetColumn(),"Phase",packet_cal.GetBlockPhase())
	    for gchannel in range(0,4):
		    #get the waveform, if only one channel/packet, only one waveform!
		    #wf_raw = packet_raw.GetWaveform(int(gchannel))
		    wf_cal = packet_cal.GetWaveform(int(gchannel))
		    #ampl_raw[group*4+gchannel][ievt]=wf_raw.GetADCArray(Nsamples)
		    #ampl_cal[group*4+gchannel][ievt]=wf_cal.GetADCArray(Nsamples)
		    ampl_cal[group*4+gchannel][ievt]=((wf_cal.GetADC16bitArray(Nsamples))/SCALE)-OFFSET

#print(firstsample)

#plt.hist(firstsample,bins=4096)
#plt.show()
#exit()

#exit()
# Filter requirements.
order = 5
fs = 1.0e9       # sample rate, Hz
cutoff = 100.0e6  # desired cutoff frequency of the filter, Hz

# Get the filter coefficients so we can check its frequency response.
b, a = butter_lowpass(cutoff, fs, order)

# Filter the data, and plot both the original and filtered signals.
y = butter_lowpass_filter(ampl_cal, cutoff, fs, order)


offset=np.mean(y[:,:,20:100],axis=2)

#print(offset[10])
#plt.plot(offset[10])
#plt.show()
#exit()
#y=y-offset[:,:,None]

xulim = 170
xllim = 70
yulim = 130
yllim = -20
xsize = 30
ysize = 20

#do some statistics on pedestal file
#rms_filt=np.mean(np.std(y[:,:,100:145],axis=2),axis=1)
#print(rms_filt)
#rms_raw=np.mean(np.std(ampl_cal[:,:,100:145],axis=2),axis=1)
#print(rms_raw)

#plt.plot(offset[33,:])
#plt.show()
#exit()


wbinsx=np.arange(100,146)
wbinsy=(np.arange(-300,1200))/10.


pbinsx=(np.arange(-20,200))

peakvalue=y[:,:,119]
#print(peakvalue)

xvalues=[]
singevals=np.arange(100,145)

for i in range (0,nevt):
    xvalues.append(singevals)
    

xvalues=np.array(xvalues)
#exit()

meanwaves=np.mean(ampl_cal[:,:,:],axis=1)
#print(meanwaves)
#print(np.argmax(np.mean(y[:,:,0:170],axis=1),axis=1))
#print(np.amax(np.mean(y[:,:,0:170],axis=1),axis=1))

#print(xvalues,len(xvalues))
#print(y[33,10,100:145].flatten())


print('Generate Some Mean Waveforms')
with PdfPages('4_Mean_waveforms.pdf') as pdf:
    for group in range(0,16):
        fig = plt.figure(figsize=(xsize, ysize))
        plt.title("Page "+str(group))
        ax1=[]
        for gchannel in range (0,4):
            ax1.append(plt.subplot(2,2,gchannel+1))
            ax1[gchannel].set_xlim([xllim, xulim])
            #ax1[gchannel].set_ylim([yllim, yulim])
            plt.title('Channel {}'.format(group*4+gchannel),fontsize=25)
            plt.xlabel('Sample in ns',fontsize=20)
            plt.ylabel('Amplitude in ADC counts',fontsize=20)
            plt.tick_params(axis='both', labelsize=20)
            plt.plot(meanwaves[group*4+gchannel])
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()

print('Generate Some unfiltered plots')
with PdfPages('0_SomeEvents_unfiltered.pdf') as pdf:
    for group in range(0,16):
        fig = plt.figure(figsize=(xsize, ysize))
        plt.title("Page "+str(group))
        ax1=[]
        for gchannel in range (0,4):
            ax1.append(plt.subplot(2,2,gchannel+1))
            #ax1[gchannel].set_xlim([xllim, xulim])
            #ax1[gchannel].set_ylim([yllim, yulim])
            plt.title('Channel {}'.format(group*4+gchannel),fontsize=25)
            plt.xlabel('Sample in ns',fontsize=20)
            plt.ylabel('Amplitude in ADC counts',fontsize=20)
            plt.tick_params(axis='both', labelsize=20)
            for event in range (0,50):
                #ax1[gchannel].plot(neu[group*4+gchannel])
                ax1[gchannel].plot(ampl_cal[group*4+gchannel][event])
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()

print('Generate Some filtered plots')
with PdfPages('1_SomeEvents_filtered.pdf') as pdf:
    for group in range(0,16):
        fig = plt.figure(figsize=(xsize, ysize))
        plt.title("Page "+str(group))
        ax1=[]
        for gchannel in range (0,4):
            ax1.append(plt.subplot(2,2,gchannel+1))
            ax1[gchannel].set_xlim([xllim, xulim])
            #ax1[gchannel].set_ylim([yllim, yulim])
            plt.title('Channel {}'.format(group*4+gchannel),fontsize=25)
            plt.xlabel('Sample in ns',fontsize=20)
            plt.ylabel('Amplitude in ADC counts',fontsize=20)
            plt.tick_params(axis='both', labelsize=20)
            for event in range (0,50):
                #ax1[gchannel].plot(neu[group*4+gchannel])
                ax1[gchannel].plot(y[group*4+gchannel][event])
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()

print('Generate Waveform histos')
with PdfPages('2_Waveform_Histo.pdf') as pdf:
    for group in range(0,16):
        fig = plt.figure(figsize=(xsize, ysize))
        plt.title("Page "+str(group))
        ax1=[]
        for gchannel in range (0,4):
            ax1.append(plt.subplot(2,2,gchannel+1))
            plt.title('Channel {}'.format(group*4+gchannel),fontsize=25)
            plt.xlabel('Sample in ns',fontsize=20)
            plt.ylabel('Amplitude in ADC counts',fontsize=20)
            plt.tick_params(axis='both', labelsize=20)
            plt.hist2d(xvalues.flatten(), y[group*4+gchannel,:,100:145].flatten(),bins=(wbinsx,wbinsy), cmap='gist_stern')
            #plt.axis((100,140,-30,70))
            plt.colorbar()
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
        
print('Generate Peak histos')
with PdfPages('3_Peak_Histo.pdf') as pdf:
    for group in range(0,16):
        fig = plt.figure(figsize=(xsize, ysize))
        plt.title("Page "+str(group))
        ax1=[]
        for gchannel in range (0,4):
            ax1.append(plt.subplot(2,2,gchannel+1))
            plt.title('Channel {}'.format(group*4+gchannel),fontsize=25)
            plt.xlabel('Peak amplitude in ADC counts',fontsize=20)
            plt.ylabel('#',fontsize=20)
            plt.tick_params(axis='both', labelsize=20)
            plt.hist(peakvalue[group*4+gchannel,:], bins=pbinsx,histtype='stepfilled')
            #plt.axis((-20,200,0,1200))
        pdf.savefig()  # saves the current figure into a pdf page
        plt.close()
