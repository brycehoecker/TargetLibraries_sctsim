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
filename="delme_1200_r1.tio"

reader = WaveformArrayReader(filename)
n_pixels = reader.fNPixels
n_samples = reader.fNSamples
n_events = reader.fNEvents

n_events = 1000

#Generate the memory to be filled in-place
waveforms = np.zeros((n_pixels, n_samples), dtype=np.float32)


#Storage cell id of the first sample of the event per pixel
first_cell_ids = np.zeros(n_pixels,dtype=np.uint16)
allsampling=np.zeros((n_events,16,128),dtype=np.uint16)
allcells=np.zeros((n_events,16,128),dtype=np.uint16)
allwaves= np.zeros((n_events,16,128), dtype=np.float32)
#allwaves= np.zeros((16, n_events,n_samples ), dtype=np.float32)

peaks=[]
for event_index in tqdm(range(0,n_events,1)):
    ret=reader.GetR1Event(event_index,waveforms)
    phase=ret[0]%32
    #print("Phase",phase)
    for i in range(0,16):
       for j in range(128):
           allcells[event_index][i][j]=phase+j
           allsampling[event_index][i][j]=(phase+j)%64
           allwaves[event_index][i][j]=waveforms[i][j]

    plot=0
    if plot==1:
        for i in range(16):
            plt.plot(waveforms[i],label="Channel {}".format(i))
        #plt.show()
        #plt.plot(waveforms[1],label="Channel 1")
        #plt.title("20mV, 10ns FWHM Gauss")
        plt.xlabel("Sample in ns")
        #plt.ylabel("Amplitude in mV (DC TF applied)")
        #plt.ylim(-10, 25)
        #plt.hlines(20,0,128,color="grey")
        #plt.hlines(-250,0,128,color="grey")
        plt.grid()
        plt.legend()
        plt.show()


print(np.mean(allwaves),np.std(allwaves))
flatw=allwaves.flatten()
flatw=flatw.flatten()
flats=allsampling.flatten()
flats=flats.flatten()
plt.hist(flatw,bins=np.arange(-10,10,.5))
plt.title("Mean: {:.2}, STD: {:.2} ADC counts".format(np.mean(flatw),np.std(flatw)))
plt.xlabel("Pedestal corrected ADC counts")
plt.show()

plt.hist2d(flats,flatw,bins=[np.arange(0,65,1),np.arange(-10,10,0.5)])
plt.colorbar()
plt.xlabel("Sampling Cell")
plt.ylabel("Pedestal corrected ADC counts")

means=[]
stds=[]
for i in range(16):
    means.append(np.mean(allwaves[:][i][:]))
    stds.append(np.std(allwaves[:][i][:]))
