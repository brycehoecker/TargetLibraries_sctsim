import matplotlib.pyplot as plt
import numpy as np
from target_io import WaveformArrayReader
import pandas as pd
from tqdm import tqdm

def reverse_bit(num):
    result = 0
    while num:
        result = (result << 1) + (num & 1)
        num >>= 1
    return result

#filename = "data/fix5_file_restart_2_r1.tio"

#filename ="data/fix7_file_restart_100_r1.tio"
#filename ="/DATA/Messungen_Adrian/CTC_Eval_Board/TC_and_T5TEA/ped_stability/data/fix12_file_restart_10_r1.tio"
filename="delme_r0.tio"
#filename="pedestal_r1.tio"

reader = WaveformArrayReader(filename)
n_pixels = reader.fNPixels
n_samples = reader.fNSamples
n_events = reader.fNEvents

#Generate the memory to be filled in-place
waveforms = np.zeros((n_pixels, n_samples),dtype=np.ushort)
#waveforms = np.zeros((n_pixels, n_samples), dtype=np.float32)
#waveforms = np.zeros((n_pixels, n_samples), dtype=np.ushort)


#Storage cell id of the first sample of the event per pixel
first_cell_ids = np.zeros(n_pixels,dtype=np.uint16)

#allwaves= np.zeros((n_events,n_samples), dtype=np.ushort)
#allwaves= np.zeros((16, n_events,n_samples ), dtype=np.float32)

allwaves=[]

#Fill the arrays
#event_timestamp_prev = 0
#tacks = []
#t_diff=[]
#allwaves = []
bins128=np.arange(0,128)
print(len(bins128))
meanvstime=[]
time_now=0
time_prev=0
delta=0
blockmean=np.zeros((5,n_events))
blockstd=np.zeros((5,n_events))
means=np.zeros(n_events)
stds=np.zeros(n_events)
deltas=np.zeros(n_events)
phases=np.zeros(n_events)

blockmean[:]=np.NaN
blockstd[:]=np.NaN
means[:]=np.NaN
stds[:]=np.NaN
deltas[:]=np.NaN
phases[:]=np.NaN

stalecount=0
delta_prev=1000
meanmean=[]
#n_events=500000
n_inrange= 0
n_remainers = 0
n_preevent= 0
n_maxamp=0
n_similar=0
for event_index in tqdm(range(0,n_events,1)):
#for event_index in tqdm(range(5,10)):
    #print(reader.GetR1Event(event_index,waveforms))
    ret=reader.GetR0Event(event_index,waveforms)
    #print(ret)
    #plt.plot(waveforms[15])

    phase=ret[0]%32
    #if ret[0]==3263:
    #    meanmean.append(np.mean(waveforms,axis=0))
        #meanmean.append(waveforms[1])
    #print("FirstCellID", ret[0], "Phase", phase)
    for i in range(0,16):

    #    wav=[]
        for j in range(128):
            allwaves.append(waveforms[i][j])
    #        wav.append((waveforms[i][j]))


        #    if i%2==1 and waveforms[i][j]>2000:
        #        waveforms[i][j]=waveforms[i][j]-2048
        #    if i%2==0 and waveforms[i][j]<2000:
        #        waveforms[i][j]=waveforms[i][j]+2048
    #plt.plot(waveforms[0],alpha=0.8)
    #plt.show()
    #    plt.plot(wav,alpha=0.8)
    #plt.plot(np.mean(waveforms,axis=0),color="black")
allwaves=np.array(allwaves)
lsb=[]
for i in allwaves:
    lsb.append(i&2)
#plt.show()



#     time_now=ret[3]
#     if event_index>1:
#         delta=(time_now-time_prev)/1000.
#     time_prev=time_now
#
#     delta_prev_i=delta_prev
#     delta_prev=delta
#
#     #if phase != 0:
#     #        continue
#
#     offset=0*4.096
#     #offset=13.825
#     width=500.
#     #width=0.1
#     deltas[event_index]=delta
#     if delta<offset:
#         continue;
#     if delta>offset+width:
#         continue;
#     n_inrange+=1
#
#
#     #if delta_prev<450 or delta<450:
#     if delta_prev_i<250: # and delta<450:
#         n_preevent+=1
#         continue
#
#     if (int(delta*1000)%4096<384) or (int(delta*1000)%4096)>(4096-288):
#         n_similar+=1
#         continue
#
#     #continue
#     if ret[1]==1:
#         stalecount+=1
#         continue
#
#     #if ret[1]!=1:
#         #stalecount+=1
#     #    continue
#
#     #plt.clf()
#     #for i in range(16):
#     #   allwaves[i,event_index]=waveforms[i]
#     #   plt.plot(waveforms[i],alpha=0.1)
#     #plt.plot(np.mean(waveforms[0:16],axis=0),color='black',alpha=0.5)
#     #plt.show()
#
#     if np.max(waveforms)>75:# or np.max(waveforms)<-50:
#         #print("event",event_index,"has bad waveform")
#         #print("max is",np.max(waveforms),"for delta",delta)
#         n_maxamp+=1
#         continue
#
#
#
#
#
#     #if phase!=8:
#     #    continue
#
#     #print(delta)
#     x_bins=bins128+phase
#     x_bins=(x_bins+(delta-offset)*1000)/4096.
#     n_remainers+=1
#     plt.plot(x_bins,np.mean(waveforms[0:16],axis=0),alpha=0.5)
#     plt.xlim(0,((width)*1000.)/4096.)
#     #plt.show()
#     #phase=ret[0]%32
#     # phases[event_index]=phase
#     # means[event_index]=(np.mean(waveforms[0:16]))
#     # stds[event_index]=(np.std(waveforms[0:16]))
#     # for s in range(5):
#     #     if s==4 and phase==0:
#     #         continue
#     #     startbin=(s*32)-phase
#     #     if s==0:
#     #         startbin=0
#     #     stopbin=(s*32)-phase+32
#     #     if s==4:
#     #         stopbin=128
#     #     blockmean[s,event_index]=np.mean(waveforms[0:16,startbin:stopbin])
#     #     blockstd[s,event_index]=np.std(waveforms[0:16,startbin:stopbin])
#
# print(n_remainers,"Events remained of",n_inrange,"(",int((n_remainers/n_inrange)*100.),"%)")
# print("Stale",stalecount)
# print("Previous Event",n_preevent)
# print("Max Anplitude",n_maxamp)
# print("Similar Block",n_similar)
# plt.xlabel("\u0394 in * 4.096µs")
# plt.ylabel("Pedestal subtraced ADC count (Mean Waveform)")
# plt.show()
    #meanarray=[]
    #if event_index<100:
    #    for i in range(128):
    #        if i < 32:
    #            meanarray.append(np.mean(waveforms[9][0:32]))
    #        if i>=32 and i <64:
    #            meanarray.append(np.mean(waveforms[9][32:64]))
    #        if i>=64 and i <96:
    #            meanarray.append(np.mean(waveforms[9][64:96]))
    #        if i>=96:
    #            meanarray.append(np.mean(waveforms[9][96:128]))
    #meanvstime.append(np.mean(waveforms))
    #print(phase)
    #print("STD:",np.std(waveforms[0:16]),"MEAN:",np.mean(waveforms[0:16]))
    #plt.plot(np.mean(waveforms[0:16],axis=0),alpha=0.9,color="grey")
    #plt.show()
    #deltas.append(delta)
    #means.append(np.mean(waveforms[0:16]))
    #stds.append(np.std(waveforms[0:16]))
    #phases.append(phase)
    #if event_index<100:
        #plt.plot(waveforms[9],alpha=0.1,color="grey")
        #plt.plot(np.mean(waveforms,axis=0),alpha=0.1,color="grey")

        #plt.plot(meanarray,alpha=0.2,color="green")

#plt.show()
#plt.hist(allwaves.flatten(),bins=np.arange(-10,10,0.2))
#plt.show()

#plt.plot(meanvstime)
#plt.show()

#for i in range(128):
#    print("Sample:",i,"Mean:",np.mean(allwaves[:,:,i]), "STD:",np.std(allwaves[:,:,i]))

#print("\n\nAll Mean:",np.mean(allwaves),"STD:",np.std(allwaves))

    #current_cpu_ns = reader.fCurrentTimeNs
    #current_cpu_s = reader.fCurrentTimeSec
    #tack = reader.fCurrentTimeTack
    #tacks.append(tack)
    #event_timestamp = ((current_cpu_s * 1E9) + np.int64(current_cpu_ns))/1000000
    #t_cpu = pd.to_datetime(np.int64(current_cpu_s * 1E9) + np.int64(current_cpu_ns),unit='ns')
    #if event_index>0:
    #    tacks.append(event_timestamp-event_timestamp_prev)
    #event_timestamp_prev=event_timestamp
    #print(t_cpu)
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
    #meanwave=np.mean(waveforms[10:12],axis=0)
    #waveselect.append(waveforms[13]-meanwave)
    #waveselect.append(waveforms[9]-meanwave)
    #if np.max((waveforms[9]-meanwave)[45:55])>30 and  np.max((waveforms[13]-meanwave)[45:55])>30:
#        t_1=np.argmax((waveforms[9]-meanwave)[45:55])
#        t_2=np.argmax((waveforms[13]-meanwave)[45:55])
#
#        t_diff.append(t_1-t_2)
    #print("####################################")
    #print(t_1,t_2)
        #firstcellid_array.append(first_cell_ids[1])
        #phase = int(first_cell_ids[1]%32)
        #phase_array.append(phase)
        #blockpos.append(int(first_cell_ids[1]/32))
        #blockval.append(np.mean(meanwave[phase+32:phase+64])-np.mean(meanwave[phase+64:phase+96]))
        #blockval_prev.append(np.mean(meanwave[phase+32:phase+64])-np.mean(meanwave[phase:phase+32]))
#    plt.plot(waveforms[9,:]-meanwave)
#    plt.plot(waveforms[13,:]-meanwave)


    #for i in range (0,1):
    #    allwaves[i][event_index]=(waveforms[i])
        #if i == 4:
            #continue
            #plt.title("CHANNEL {}".format(i))

#print("{} Events Stale".format(stalecount))

#allwaves=np.array(allwaves)
#blockdiff = []
# xvals = []
# for j in range(len(waveselect)):
#     xvals.append(np.arange(len(waveselect[1])))
# #for j in range(1,len(blockval)):
#     #blockdiff.append(blockval[j]-blockval[j-1])
# #print(waveselect)
# #print(len(xvals[1]))
# print("###########")
# print("Mean",np.mean(t_diff),"RMS",np.std(t_diff))
# plt.hist(t_diff,bins=np.arange(20)-10)
# plt.show()


#samples=[]

#for i in range (16):
#    samples.append(allwaves[i].flatten())
#    print("Channel",i,"Mean",np.mean(samples[i]),"Sigma",np.std(samples[i]), "Var",np.var(samples[i]))

#plt.hist(allwaves,bins=10)
#plt.show()



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
