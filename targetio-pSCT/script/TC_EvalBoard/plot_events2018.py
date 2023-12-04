import target_driver
import target_io
import matplotlib.pyplot as plt
import numpy as np
import pdb
from scipy.signal import butter, lfilter, freqz
import scipy


def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y


# Filter requirements.
order = 5
fs = 1.0e9       # sample rate, Hz
cutoff = 100.0e6  # desired cutoff frequency of the filter, Hz

# Get the filter coefficients so we can check its frequency response.
b, a = butter_lowpass(cutoff, fs, order)

filename_raw = "file_r0.tio"
filename_cal = "low_intensity_r1.tio"

Nsamples = 4*32
channel=3
SCALE=13.6
OFFSET=700

#reader_raw = target_io.EventFileReader(filename_raw)
reader_cal = target_io.EventFileReader(filename_cal)
NEvents  = reader_cal.GetNEvents()

print(NEvents, "events read")

#ampl_raw = np.zeros([NEvents,Nsamples])


#f, ax = plt.subplots(3, sharex=True)
#ax = plt.subplot(211)
#ax[0].set_title("raw ADC counts",fontsize=10)
#ax[1].set_title("pedestal substracted ADC counts", fontsize=10)
#ax[2].set_title("common mode corrected ADC counts", fontsize=10)

#ax_cal =plt.subplot(211)
#ax_cal.set_xlabel("sample",fontsize=14)
#ax_cal.set_ylabel("pedestal substracted ADC counts", fontsize=14)
#ax_cal.set_title("Channel "+str(channel))

nevt = 0

timestamp=0
timestamp_prev=0

if nevt==0:
    nevt=NEvents

ampl_cal = np.zeros([nevt,Nsamples])
ampl_cmc = np.zeros([nevt,Nsamples])
maximums = np.zeros([nevt])
filtered_all = np.zeros([nevt,Nsamples])
delta_time= np.zeros([nevt])

for ievt in range(1,nevt):
    if (ievt%1000==0):
        print("Event {} of {}".format(ievt,nevt))
    event_head = target_driver.EventHeader()
    ret=reader_cal.GetEventHeader(ievt,event_head)
    #get timestamp in ns from event header
    timestamp=event_head.GetTACK()
    delta_time[ievt]=(timestamp-timestamp_prev)/1000.
    #print("Event ",ievt, " Timestamp in ns",timestamp, " Time since last Event in us ",(timestamp-timestamp_prev)/1000.)
    timestamp_prev=timestamp
    #first get the right packet from event, if only one channel/packet, then packetnumber = channel
    #rawdata_raw = reader_raw.GetEventPacket(ievt,channel)
    rawdata_cal = reader_cal.GetEventPacket(ievt,0)
    #packet_raw = target_driver.DataPacket()
    packet_cal = target_driver.DataPacket()
    #packet_raw.Assign(rawdata_raw, reader_raw.GetPacketSize())
    packet_cal.Assign(rawdata_cal, reader_cal.GetPacketSize())
    
    #get the waveform, if only one channel/packet, only one waveform!
    #wf_raw = packet_raw.GetWaveform(0)
    wf_cal = packet_cal.GetWaveform(channel)

    for sample in range(Nsamples):
        #ampl_raw[ievt,sample] = wf_raw.GetADC(sample)
        ampl_cal[ievt,sample] = ((wf_cal.GetADC16bit(sample))/SCALE)-OFFSET
        
    #common mode correction
    for otherchan in range(6,16):
        
        wf_cmc = packet_cal.GetWaveform(otherchan)
        #dircetly access the full array (faster)
        adc = np.zeros(Nsamples, dtype=np.float)
        adc=wf_cmc.GetADC16bitArray(Nsamples)
        ampl_cmc[ievt] = ampl_cmc[ievt]+ (((adc/SCALE)-OFFSET)*1/10)
   
    #ax[0].plot(ampl_raw[ievt],alpha=0.7)
    #ax[1].plot(ampl_cal[ievt],alpha=0.7)
    #filtered_wave=ampl_cal[ievt]-ampl_cmc[ievt]
    filtered_wave=butter_lowpass_filter(ampl_cal[ievt],cutoff, fs, order)

    tmax = int(np.where( filtered_wave == filtered_wave.max())[0][0])
    #maximums[ievt]=filtered_wave[70]
    maximums[ievt]=np.sum(filtered_wave[63:76])
    #print(tmax)
    filtered_wave=np.roll(filtered_wave,0)
    filtered_all[ievt]=np.roll(ampl_cal[ievt]-ampl_cmc[ievt],70-tmax)
    if (filtered_wave.max()>0 and ievt<100):
        plt.plot(filtered_wave,alpha=0.1)


plt.show()

mean=np.mean(filtered_all,axis=0)
plt.plot(mean)

plt.show()

plt.hist(maximums,bins=600)

plt.show()

#plt.plot(delta_time[1:])
#plt.hist(delta_time[1:],bins=(np.arange(249900,250100))/1000)
print ("Mean of Distribution is", np.mean(maximums))

#plt.show()