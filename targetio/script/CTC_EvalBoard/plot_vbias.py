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
#filename="/DATA/Messungen_Adrian/CTC_Eval_Board/CTC_and_CT5TEA/DC_TF/data/amplitude_1200_r0.tio"
filename=["vbias1000_r0.tio","vbias1200_r0.tio","vbias1200_r0.tio","vbias1400_r0.tio","vbias1600_r0.tio","vbias1800_r0.tio"]
vbias=[1000,1200,1400,1600,1800]
#filename="selme_r0.tio"
#filename2="/DATA/Messungen_Adrian/CTC_Eval_Board/CTC_and_CT5TEA/DC_TF/data/amplitude_phase0_1200_r0.tio"
#filename="pedestal_r1.tio"

reader = WaveformArrayReader(filename[0])
n_pixels = reader.fNPixels
n_samples = reader.fNSamples
n_events = reader.fNEvents

#reader2 = WaveformArrayReader(filename2)
#n_pixels2 = reader2.fNPixels
#n_samples2 = reader2.fNSamples
#n_events2 = reader2.fNEvents
allwaves = np.zeros((10, n_samples),dtype=np.ushort)
#Generate the memory to be filled in-place
waveforms = np.zeros((n_pixels, n_samples),dtype=np.ushort)
#waveforms2 = np.zeros((n_pixels2, n_samples2),dtype=np.ushort)
#Storage cell id of the first sample of the event per pixel
first_cell_ids = np.zeros(n_pixels,dtype=np.uint16)
normalizer=0
count=0
for file in filename:
    print(file,count)
    reader = WaveformArrayReader(file)
    for event_index in tqdm(range(0,1,1)):
        ret=reader.GetR0Event(event_index,waveforms)
        phase=ret[0]%32
        firstcell=ret[0]
        print("FirstCellID",ret[0],"Phase",phase)
        #for i in range(128)
        if count==0:
            normalizer=waveforms[0][0]
        allwaves[count]=waveforms[0]
    count+=1

plt.ylabel('normalized ADC counts')
plt.xlabel('cell')
for i in range(5):
    print(normalizer,allwaves[i][0])
    plt.plot(allwaves[i]*float(normalizer)/allwaves[i][0],alpha=0.8,label=vbias[i])#,color="black")
plt.legend(title="Vbias")
plt.show()
