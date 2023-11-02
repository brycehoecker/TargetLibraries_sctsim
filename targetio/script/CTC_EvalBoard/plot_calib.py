import matplotlib.pyplot as plt
import numpy as np
from target_io import WaveformArrayReader
import pandas as pd
from tqdm import tqdm

#chan=1

path="/DATA/Messungen_Adrian/CTC_Eval_Board/TC_and_T5TEA/ped_stability"


temp=np.loadtxt("{}/data/temperatures_pedtest_fix11.txt".format(path))

n_peds=80

temp_file=np.zeros(n_peds)

for i in range(0,n_peds):

    filename = "{}/data/fix11_file_restart_{}_r0.tio".format(path,i)
    if i==23:
        filename = "{}/data/fix11_file_restart_{}_r0.tio".format(path,22)
    reader = WaveformArrayReader(filename)
    n_pixels = reader.fNPixels
    n_samples = reader.fNSamples
    n_events = reader.fNEvents
    waveforms = np.zeros((n_pixels, n_samples), dtype=np.ushort)
    temparray=[]
    for event_index in tqdm(range(2,n_events,500)):
        retvals=reader.GetR0Event(event_index,waveforms)
        temparray.append(np.interp(retvals[4],temp[:,0],temp[:,2]))
    meantemp=np.mean(temparray)
    print("For File",filename,"temperature was",meantemp)
    temp_file[i]=meantemp


for chan in range(10,11):
    for i in range(50,51):
    #for i in ([3,5,7,8]):
        average_waveform=[]
        rms_all=[]

        for j in range(0,n_peds,1):

        #for j in ([3,5,7,8]):

            time_prev=0
            time_now=0
            delta=0.
            #filename = "{}/data/fix11_file_i{}_p{}_r1.tio".format(path,i,j)
            filename = "{}/data/fix11_file_i{}_p{}_r1.tio".format(path,j,i)
            if j==23:
                filename = "{}/data/fix11_file_i{}_p{}_r1.tio".format(path,22,i)

            reader = WaveformArrayReader(filename)

            n_pixels = reader.fNPixels
            n_samples = reader.fNSamples
            n_events = reader.fNEvents
            n_events=10000
            waveforms = np.zeros((n_pixels, n_samples), dtype=np.float32)
            allwaves= np.zeros((16, n_events,n_samples), dtype=np.float32)
            allwaves[:]=np.NaN
            allwaves2=[]
            allwavesdings=[]
            timediffs=[]
            for event_index in tqdm(range(2,n_events)):
            #for event_index in tqdm(range(5,10)):
                #print(reader.GetR1Event(event_index,waveforms))
                ret=reader.GetR1Event(event_index,waveforms)
                time_now=ret[3]
                if event_index>2:
                    delta=(time_now-time_prev)/1000.
                time_prev=time_now
                if delta<400:
                   continue
                if ret[1]==1:
                    print("Stale")
                    continue
                #if delta>600:
                #      continue
                #if ret[0]%32!=0:
                #    continue
                #temparray.append(np.interp(retvals[4],temp[:,0],temp[:,1]))
                #print(temperature)
                #if np.max(waveforms>10):
                #    print("event",event_index,"has bad waveform")
                #    continue
                for ii in range(16):
                    #if ii == 0:
                    #    print (event_index)
                    allwaves[ii,event_index]=waveforms[ii]
                #timediffs.append(delta)
                #allwaves2.append(np.mean(waveforms[0:16],axis=0))
                #allwavesdings.append(list(waveforms[10]))
                #if event_index<400:
                    #plt.plot(waveforms[ii],alpha=1)
                    #plt.show()
            #for jj in range(1,10):
            #    plt.plot(allwaves[chan,jj],alpha=0.5)
            #plt.show()
            #allwaves=np.array(allwaves)
            #meanwave=np.mean(allwaves[:,:,32:64],axis=1)
            #print(allwaves)
            #allwaves2=np.array(allwavesdings)
            #if j==100:
            #    exit()
            meanwave=np.nanmean(allwaves[:,:,:],axis=1)
            #meanwave=np.nanmean(meanwave,axis=0)

            #allwaves2=np.array(allwaves2)
            #print(allwaves2.shape)
            #meanwave2=np.mean(allwaves2,axis=0)
            #print(meanwave2.shape)

            #plt.plot(meanwave2)
            #plt.plot(meanwave)
            #plt.show()
            rmswave=np.zeros(16)
            #for tau in range(16):
                #rmswave[tau]=np.std(allwaves[tau,:,32:64])
                #rmswave[tau]=np.std(allwaves[:,:,32:64])
            #meanwave=np.mean(meanwave,axis=0)
            average_waveform.append(meanwave)
            rmswave[0]=np.nanstd(allwaves)
            rms_all.append(rmswave[0])
        average_waveform=np.array(average_waveform)
        #for iii in range(350):
        #    if np.abs(temp_file[iii]-27)<0.25:
        #        print(iii,rms_all[iii][0])
        #continue
        rms_all=np.array(rms_all)
        fig, axs = plt.subplots(5, 6,figsize=(10,8))
        for k in range(0,n_peds,10):
            index=int(k/10)
            print(k)
            #print(i,int(i/6),int(i%5))
            try:
                if (k==(i)):
                    #axs[int(index/6),int(index%6)].plot(average_waveform[k,chan],color="orange",lw=1)
                    axs[int(index/6),int(index%6)].plot(np.mean(average_waveform[k],axis=0),color="orange",lw=1)
                    #axs[int(index/6),int(index%6)].plot(average_waveform[k],color="orange",lw=1)
                else:
                    #axs[int(index/6),int(index%6)].plot(average_waveform[k,chan],color="blue",lw=1)
                    axs[int(index/6),int(index%6)].plot(np.mean(average_waveform[k],axis=0),color="blue",lw=1)
                    #axs[int(index/6),int(index%6)].plot(average_waveform[k],color="blue",lw=1)
            except:
                pass
            axs[int(index/6),int(index%6)].set_title("File {}".format(k),size=7)
            axs[int(index/6),int(index%6)].set_ylim(-5,2.5)
            axs[int(index/6),int(index%6)].text(2, -3.5, 'T {:.2f} °C\nSTD {:.2f} ADC counts'.format(temp_file[k],rms_all[k]), size=6,bbox={'facecolor': 'white', 'alpha': 0.5, 'pad': 3})
            if index%6!=0:
                plt.setp(axs[int(index/6),int(index%6)].get_yticklabels(), visible=False)
            if index/6!=5:
                plt.setp(axs[int(index/6),int(index%6)].get_xticklabels(), visible=False)

        #plt.savefig("plots/fix10_file_i_chan_{}_file_{}_tcut400.png".format(chan,i))
        plt.savefig("{}/plots/fix11_mean_file_{}_tcut400.png".format(path,i))
        #plt.savefig("plots/fix4_chan_{}_file_{}.pdf".format(chan,i))
        #continue
        plt.clf()
        for jay in range(1):
            plt.clf()
            plt.scatter(temp_file-31.81,rms_all)
            plt.xlabel("T-T(ped 50) in °C")
            plt.ylabel("STD in ADC counts")
            #plt.savefig("plots/fix8_temp_vs_std_chan_{}_file_{}.png".format(jay,i))
            plt.savefig("{}/plots/fix11_temp_vs_std_file_{}_tcut400.png".format(path,i))
