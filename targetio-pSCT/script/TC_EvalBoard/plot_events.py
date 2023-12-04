import target_driver
import target_io
import matplotlib.pyplot as plt
import numpy as np
import pdb
#import calibrateWF

calibrate=False

if calibrate:
    calibWF=calibrateWF.calibrateWF("/home/cta/luigi/TC_EvalBoard/data/20160620/TF_TD250_4b/TFdata.npz")

plt.ion()
#filename = "/home/cta/luigi/TC_EvalBoard/data/20160517/bd1_PUbias_coarse/PUbias_2500/TFdata_VpedDAC_2055.fits"
#filename = "/home/cta/luigi/TC_EvalBoard/data/20160524_2/TF_measure/Isel_2467/TFdata_VpedDAC_1500.fits"
filename = "/lab1tb/checM/2016-09-01/16-24-16.fits"
Nsamples = 13*32
sample0=0

reader = target_io.EventFileReader(filename)

NEvents  = reader.GetNEvents()

print NEvents, "events read"


for channel in range(16):
    ampl = np.zeros([NEvents,Nsamples])
    ax = plt.subplot(111)
    ax.set_xlabel("sample",fontsize=14)
    if calibrate:
        ax.set_ylabel("amplitude (mV)", fontsize=14)
    else:
        ax.set_ylabel("raw ADC counts", fontsize=14)
    for ievt in range(1):#NEvents):
        rawdata = reader.GetEventPacket(ievt,channel)#second entry is asic/channel, only one enabled in this case
        packet = target_driver.DataPacket()
        packet.Assign(rawdata, reader.GetPacketSize())
        wf = packet.GetWaveform(0)
        for sample in range(Nsamples):
            ampl[ievt,sample] = wf.GetADC(sample0+sample)
        #ax.plot(ampl[ievt])
        if calibrate:
            calampl=calibWF.calibrate(ampl[ievt],channel)
            ax.plot(calampl,linewidth=0,marker='.',color='k')
            #ax.plot(calampl)
        else:
            #if np.all(ampl[ievt]>500):
            ax.plot(ampl[ievt],linewidth=0,marker='.',color='k')
    rms = np.std(ampl,axis=0)
    rms = np.average(rms)
    print "average baseline RMS: {} ADC counts".format(rms) 
    ax.set_title("Channel "+str(channel))
    plt.show()
    pdb.set_trace()
    ax.clear()
    del ax



