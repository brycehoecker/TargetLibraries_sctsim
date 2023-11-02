import matplotlib.pyplot as plt
import numpy as np
from target_io import WaveformArrayReader
import pandas as pd
from tqdm import tqdm
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
zerocells=[]
allwaves=[]
peaks=[]
for event_index in tqdm(range(0,n_events,1)):
    ret=reader.GetR1Event(event_index,waveforms)
    phase=ret[0]%32
    plot=1
    if event_index==0:
        print("Phase",phase)
    for j in range(1,127):
           if waveforms[0][j-1]>0 and waveforms[0][j+1]<0 and waveforms[0][j]<0:
               zerocells.append((phase+j)%64)
               if plot==1:
                   plt.vlines(j,-200,200,color="red")


    if plot==1:
        plt.plot(waveforms[0],label="Channel 0")
        #plt.show()
        #plt.plot(waveforms[1],label="Channel 1")
        #plt.title("20mV, 10ns FWHM Gauss")
        #plt.xlabel("Sample in ns")
        #plt.ylabel("Amplitude in mV (DC TF applied)")
        #plt.ylim(-10, 2
        #plt.hlines(20,0,128,color="grey")
        #plt.hlines(-250,0,128,color="grey")
        plt.grid()
        plt.legend()
        plt.show()

plt.hist(zerocells,bins=64)
plt.xlabel("Sampling Cell")
plt.ylabel("Occupation")
plt.show()

exit()
allwaves=np.array(allwaves)
print(np.mean(allwaves),np.std(allwaves))
