import matplotlib.pyplot as plt
import numpy as np
from target_io import WaveformArrayReader
import pandas as pd
from tqdm import tqdm

filename = "run_r0.tio"

reader = WaveformArrayReader(filename)
n_pixels = reader.fNPixels
n_samples = reader.fNSamples
n_events = reader.fNEvents

#Generate the memory to be filled in-place
#waveforms = np.zeros((n_pixels, n_samples),dtype=np.ushort)
waveforms = np.zeros((n_pixels, n_samples), dtype=np.float32)
#waveforms = np.zeros((n_pixels, n_samples), dtype=np.ushort)

waveselect = []
#blockpos = []
#blockval = []
#blockval_prev = []
#phase_array=[]
#firstcellid_array = []
#cellvals = []
#cellpos = []
#for i in range (4096):
        #cellvals.append([])
        #cellpos.append([])

#Storage cell id of the first sample of the event per pixel
first_cell_ids = np.zeros(n_pixels,dtype=np.uint16)

#Fill the arrays
event_timestamp_prev = 0
tacks = []
t_diff=[]
for event_index in tqdm(range(0,int(n_events/1))):
    reader.GetR1Event(event_index,waveforms,first_cell_ids)

    current_cpu_ns = reader.fCurrentTimeNs
    current_cpu_s = reader.fCurrentTimeSec
    #tack = reader.fCurrentTimeTack
    #tacks.append(tack)
    event_timestamp = ((current_cpu_s * 1E9) + np.int64(current_cpu_ns))/1000000
    t_cpu = pd.to_datetime(np.int64(current_cpu_s * 1E9) + np.int64(current_cpu_ns),unit='ns')
    if event_index>0:
        tacks.append(event_timestamp-event_timestamp_prev)
    event_timestamp_prev=event_timestamp
    print(t_cpu)
    #print(event_timestamp)
    #i=0
    #for t in waveforms[1]:
    #    cellvals[int((first_cell_ids[1]+i)%4096)].append(t)
    #    cellpos[int((first_cell_ids[1]+i)%4096)].append(int(first_cell_ids[1]/32))
    #    i+=1
    #if (tack%32==16):
    #print("first cell id",first_cell_ids[1])
    #if True:
    #if int(first_cell_ids[1]/32) == 10:
    meanwave=np.mean(waveforms[10:12],axis=0)
    waveselect.append(waveforms[13]-meanwave)
    waveselect.append(waveforms[9]-meanwave)
    if np.max((waveforms[9]-meanwave)[45:55])>30 and  np.max((waveforms[13]-meanwave)[45:55])>30:
        t_1=np.argmax((waveforms[9]-meanwave)[45:55])
        t_2=np.argmax((waveforms[13]-meanwave)[45:55])
    
        t_diff.append(t_1-t_2)
    #print("####################################")
    #print(t_1,t_2)
        #firstcellid_array.append(first_cell_ids[1])
        #phase = int(first_cell_ids[1]%32)
        #phase_array.append(phase)
        #blockpos.append(int(first_cell_ids[1]/32))
        #blockval.append(np.mean(meanwave[phase+32:phase+64])-np.mean(meanwave[phase+64:phase+96]))
        #blockval_prev.append(np.mean(meanwave[phase+32:phase+64])-np.mean(meanwave[phase:phase+32]))
    plt.plot(waveforms[9,:]-meanwave)
    plt.plot(waveforms[13,:]-meanwave)
    #for i in range (0,16):
        #if i == 4:
            #continue
        #plt.plot(waveforms[i,:])
    plt.show()

#blockdiff = []
xvals = []
for j in range(len(waveselect)):
    xvals.append(np.arange(len(waveselect[1])))
#for j in range(1,len(blockval)):
    #blockdiff.append(blockval[j]-blockval[j-1])
#print(waveselect)
#print(len(xvals[1]))
print("###########")
print("Mean",np.mean(t_diff),"RMS",np.std(t_diff))
plt.hist(t_diff,bins=np.arange(20)-10)
plt.show()

#plt.hist(cellvals[100])
#plt.scatter(cellvals[100],cellpos[100])
#heatmap, xedges, yedges = np.histogram2d(cellvals[100],cellpos[100], bins=[30,128])

#heatmap, xedges, yedges = np.histogram2d(blockpos,blockval, bins=[128,30])
#heatmap, xedges, yedges = np.histogram2d(xvals,waveselect, bins=[256,30])

#extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]

#plt.clf()
#plt.hist(blockval)
#plt.hist(blockdiff)
#plt.imshow(heatmap.T, extent=extent, origin='lower')
#plt.show()

#plt.clf()

#plt.plot(tacks)
#plt.show()
