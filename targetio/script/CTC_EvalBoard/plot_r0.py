import matplotlib.pyplot as plt
import numpy as np
from target_io import WaveformArrayReader
import pandas as pd
from tqdm import tqdm

chan=5
colors = ["","red","red","blue","blue","blue","green","green"]

for i in range(1,6):
            filename = "data/fix4_file_restart_{}_r0.tio".format(i)

            reader = WaveformArrayReader(filename)

            n_pixels = reader.fNPixels
            n_samples = reader.fNSamples
            n_events = reader.fNEvents
            allwaves=np.zeros((n_events, n_samples),dtype=np.ushort)
            waveforms = np.zeros((n_pixels, n_samples), dtype=np.ushort)

            for event_index in range(1,n_events): # tqdm(range(1,10)):
            #for event_index in tqdm(range(5,10)):
                #print(reader.GetR0Event(event_index,waveforms))
                reader.GetR0Event(event_index,waveforms)
                #plt.plot(waveforms[5],alpha=0.7,color=colors[i],label="file {}".format(i))
                #if np.max(waveforms>10):
                #    print("event",event_index,"has bad waveform")
                #    continue
                #for ii in range(16):
                allwaves[event_index]=(waveforms[chan])
                #print(waveforms[chan])
                #plt.plot(waveforms[chan])
                #plt.show()
                #if event_index<400:
                #plt.plot(waveforms[0],alpha=0.2)
            #plt.show()
            #for j in range(1,10):
            #    plt.plot(allwaves[j],alpha=0.2)
            #allwaves=np.array(allwaves)
            #print(allwaves.shape)

            #plt.show()
            plt.plot(np.mean(allwaves[1:n_events],axis=0),alpha=0.7,color=colors[i],label="file {}".format(i),lw=1)
            #meanwave=np.mean(allwaves,axis=1)
            #meanwave=np.mean(meanwave,axis=0)
            #average_waveform.append(meanwave)
        #average_waveform=np.array(average_waveform)

        #fig, axs = plt.subplots(5, 6,figsize=(10,8))
        #for k in range(30):
            #print(i,int(i/6),int(i%5))
        #    try:
        #        if (k==(i-1)):
        #            axs[int(k/6),int(k%6)].plot(average_waveform[k][chan],color="orange",lw=1)
        #        else:
        #            axs[int(k/6),int(k%6)].plot(average_waveform[k][chan],color="blue",lw=1)
        #    except:
        #        pass
        #    axs[int(k/6),int(k%6)].set_title("Ped {}".format(k+1),size=7)
        #    axs[int(k/6),int(k%6)].set_ylim(-6,6)
        #    if k%6!=0:
        #        plt.setp(axs[int(k/6),int(k%6)].get_yticklabels(), visible=False)
        #    if k/6!=5:
        #        plt.setp(axs[int(k/6),int(k%6)].get_xticklabels(), visible=False)
        #plt.savefig("plots/fix2_chan_{}_file_{}.png".format(chan,i))
        #plt.savefig("plots/fix2_chan_{}_file_{}.pdf".format(chan,i))
        #plt.clf()
plt.legend()
plt.show()
