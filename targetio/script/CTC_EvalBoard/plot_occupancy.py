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
filename="delme_r0.tio"
#filename2="/DATA/Messungen_Adrian/CTC_Eval_Board/CTC_and_CT5TEA/DC_TF/data/amplitude_phase0_1200_r0.tio"
#filename="pedestal_r1.tio"

reader = WaveformArrayReader(filename)
n_pixels = reader.fNPixels
n_samples = reader.fNSamples
n_events = reader.fNEvents

#reader2 = WaveformArrayReader(filename2)
#n_pixels2 = reader2.fNPixels
#n_samples2 = reader2.fNSamples
#n_events2 = reader2.fNEvents

#Generate the memory to be filled in-place
waveforms = np.zeros((n_pixels, n_samples),dtype=np.ushort)
#waveforms2 = np.zeros((n_pixels2, n_samples2),dtype=np.ushort)
#Storage cell id of the first sample of the event per pixel
first_cell_ids = np.zeros(n_pixels,dtype=np.uint16)


allwaves=[]
allcells=[]
wilkclk="104MHz"
#if n_events>50:
#    n_events=50
firstcell=-100
event_count=np.max([n_events,2])#,n_events2])

for event_index in tqdm(range(0,event_count,1)):
    ret=reader.GetR0Event(event_index,waveforms)
    #print(ret)
    #ret2=reader2.GetR0Event(event_index,waveforms2)

    #phase=ret[0]%32
    #if event_index==0:
    #    firstcell=ret[0]
        #print(firstcell)
    #phase2=ret2[0]%32
    #print("FirstCellID",ret[0],"Phase",phase)
    #print("FirstCellID_2",ret2[0],"Phase",phase2)
    #for i in range(0,1):

    wav=[]
    #cells=[]
    for i in range(0,16):
        for j in range(n_samples):
            #cells.append((j+ret[0])%16384)
            #allcells.append(j+ret[0]%16384)
            allwaves.append(waveforms[i][j])
        #allwaves.append(waveforms[0][j])

    #plt.plot(cells,waveforms[0],alpha=0.8,color='blue'),#marker=',',ls='')

    #newwave=[]
    #for j in range(n_samples):
        #if j%64>31:
        #    newwave.append(np.nan)
        #else:
    #        newwave.append(waveforms[0][j])
    #plt.ylabel('ADC count')
    #plt.plot(newwave)
    #plt.plot(waveforms[0],alpha=0.8)#,color="black")
    #plt.show()
    #t=waveforms[0]
    #print(t[0])
    #for i in range(n_samples):
    #    allcells.append((ret[0]+i)%16384)
    #    allwaves.append(waveforms[0][i])
allwaves=np.array(allwaves)

plt.hist(allwaves,np.arange(0,4096,1))
plt.title("All, {}".format(wilkclk))
plt.show()

plt.clf()
plt.hist(allwaves%64,np.arange(-.5,63.6,1))
plt.title("Mod 64, {}".format(wilkclk))
plt.savefig("/home/cta/{}_mod64.png".format(wilkclk))
plt.show()
#print(np.arange(-.5,15.6,1))
plt.clf()
plt.hist(allwaves%32,np.arange(-.5,31.6,1))
plt.title("Mod 32, {}".format(wilkclk))
plt.savefig("/home/cta/{}_mod32.png".format(wilkclk))
#plt.show()


plt.clf()
plt.hist(allwaves%16,np.arange(-.5,15.6,1))
plt.title("Mod 16, {}".format(wilkclk))
plt.savefig("/home/cta/{}_mod16.png".format(wilkclk))
#plt.show()

plt.clf()
plt.hist(allwaves%8,np.arange(-.5,7.6,1))
plt.title("Mod 8, {}".format(wilkclk))
plt.savefig("/home/cta/{}_mod08.png".format(wilkclk))
#plt.show()

plt.clf()
plt.hist(allwaves%4,np.arange(-.5,3.6,1))
plt.title("Mod 4, {}".format(wilkclk))
plt.savefig("/home/cta/{}_mod04.png".format(wilkclk))
#plt.show()

plt.clf()
plt.hist(allwaves%2,np.arange(-.5,1.6,1))
plt.title("Mod 2")
plt.savefig("/home/cta/{}_mod02.png".format(wilkclk))
#plt.show()

exit()


#plt.xlabel('ns')
#plt.show()
allwaves=np.array(allwaves[0:16384])
allcells=np.array(allcells[0:16384])
index=np.argsort(allcells)
allwaves=(allwaves[index])
allcells=allcells[index]
plt.title('FirstCellID {}'.format(firstcell))
#allwaves=np.array(allwaves).flatten()
#print(firstcell)
ncells=16384

#waves_resort=np.zeros(16384)
#for k in range(4):
#    for i in range(128):
#        for j in range(32):
#            #print(i*32+j+k*4096)
#            if i%2==0:
#                waves_resort[i*32+j+k*4096]=allwaves[(int(i/2)*32+j+k*4096)%ncells]
#            else:
#                waves_resort[(i*32+j+k*4096)]=allwaves[(int((i/2)+1)*32+j+2048+k*4096)%ncells]

#plt.subplot(211)
plt.title("order raw")
plt.plot(allcells,allwaves,alpha=0.8)
plt.vlines(firstcell,np.min(allwaves),np.max(allwaves),color="red")
for i in range(8):
    plt.vlines(i*2048,np.min(allwaves),np.max(allwaves),color="black")
#plt.subplot(212)
#plt.title("reorder blocks")
#plt.plot(allcells,waves_resort,alpha=0.8)
#for i in range(8):
#    plt.vlines(i*2048,np.min(allwaves),np.max(allwaves),color="black")
plt.xlabel('ns')
plt.show()

#allwaves=np.array(allwaves)
#allcells=np.array(allcells)

#plt.hist2d(allcells,allwaves,bins=(16384,32))
#plt.hist(allwaves,bins=np.arange(0,4096,1))
#plt.hist(allwaves,bins=np.arange(0,16,1))
#plt.show()

#lsb=[]
#for i in allwaves:
#    lsb.append(i&2)
