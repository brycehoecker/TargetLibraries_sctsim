import matplotlib.pyplot as plt
import numpy as np
from target_io import WaveformArrayReader
import pandas as pd
from tqdm import tqdm
from scipy.ndimage import gaussian_filter1d
from scipy import signal
import matplotlib as mpl
mpl.use('TkAgg')

def reverse_bit(num):
    result = 0
    while num:
        result = (result << 1) + (num & 1)
        num >>= 1
    return result

#filename = "data/fix5_file_restart_2_r1.tio"

#filename ="data/fix7_file_restart_100_r1.tio"
#filename ="/DATA/Messungen_Adrian/CTC_Eval_Board/TC_and_T5TEA/ped_stability/data/fix12_file_restart_10_r1.tio"
#ilename="/DATA/Messungen_Adrian/CTC_Eval_Board/CTC_and_CT5TEA/DC_TF/data/amplitude_8
#00_r1.tio"
filename="delme_r1.tio"

reader = WaveformArrayReader(filename)
n_pixels = reader.fNPixels
n_samples = reader.fNSamples
n_events = reader.fNEvents

#Generate the memory to be filled in-place
waveforms = np.zeros((n_pixels, n_samples), dtype=np.float32)


#Storage cell id of the first sample of the event per pixel
first_cell_ids = np.zeros(n_pixels,dtype=np.uint16)

#allwaves= np.zeros((n_events,n_samples), dtype=np.ushort)
#allwaves= np.zeros((16, n_events,n_samples ), dtype=np.float32)

allwaves=[]
peaks=[]
for event_index in tqdm(range(0,n_events,1)):
    ret=reader.GetR1Event(event_index,waveforms)
    phase=ret[0]%32
    block=int(ret[0]/32)
    print("Phase",phase)
    #
    #for i in range(0,2):
    #   for j in range(128):
#           allwaves.append(waveforms[i][j])

    plot=1
    wave=waveforms[0]
    if plot==1:
        plt.hlines(0,0,128,color="grey")
        #plt.hlines(115,0,128,color="grey")
        ymin=-10.
        ymax=50.
        yrange=ymax-ymin
        xraw=np.arange(0,128,1)
        xfilt=np.arange(0,128,0.1)
        x1=0
        if phase<20:
            plt.text(1,ymax-(yrange/10.),"{}".format(block))
        while True:

            block=block+1
            xvalue=(32-phase) + (x1*32)
            if xvalue>127:
                break
            plt.vlines(xvalue,ymin,ymax,color="grey",alpha=0.5)
            if xvalue<116:
                plt.text(xvalue+1,ymax-(yrange/10.),"{}".format(block))
            x1+=1
        for k in range(1):
            wave=waveforms[k]
            if k==0:
                f = signal.resample(wave, 1280)
                gauss_std = 20 #resample has 10 times the points -> 10 * std
                filtered_f = gaussian_filter1d(f, gauss_std)
                plt.plot(xfilt,filtered_f,label="Channel 0 filtered",alpha=0.9)
            plt.plot(xraw,wave,label="Channel {}".format(k),alpha=0.9)
            if np.max(wave)>50:
                print("Channel {} on".format(k))

        #plt.title("115mV, 10.4ns FWHM Gauss")
        plt.xlabel("Sample in ns")
        #plt.ylabel("Amplitude in mV (DC TF applied)")
        plt.ylim(ymin, ymax)
        plt.xlim(0, 128)
        #plt.hlines(20,0,128,color="grey")
        #plt.hlines(-250,0,128,color="grey")
        #plt.grid()
        #plt.legend()
        plt.show()


#allwaves=np.array(allwaves)
#print(np.mean(allwaves),np.std(allwaves))
