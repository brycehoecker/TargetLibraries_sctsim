import target_driver
import target_io
import matplotlib.pyplot as plt
import numpy as np

#filename = "/home/cta/luigi/TC_EvalBoard/data/20160517/bd1_PUbias_coarse/PUbias_2500/TFdata_VpedDAC_2055.fits"
#filename = "/home/cta/luigi/TC_EvalBoard/data/20160524_2/TF_measure/Isel_2467/TFdata_VpedDAC_1500.fits"
filename = "/home/cta/luigi/TC_EvalBoard/data/20160530/test/test_sine.fits"
Nsamples = 96

reader = target_io.EventFileReader(filename)

NEvents  = reader.GetNEvents()

print NEvents, "events read"

ax = plt.subplot(111)

vals = np.array([])

for ievt in range(NEvents):
    rawdata = reader.GetEventPacket(ievt,0)#second entry is asic/channel, only one enabled in this case
    packet = target_driver.DataPacket()
    packet.Assign(rawdata, reader.GetPacketSize())
    wf = packet.GetWaveform(0)
    ampl=np.zeros(Nsamples)
    for sample in range(Nsamples):
        ampl[sample] = wf.GetADC(12+sample)
    vals=np.append(vals,ampl)

nbins = np.max(vals)-np.min(vals)
n, bins, patches = plt.hist(vals, nbins, normed=0, facecolor='green', log=True, alpha=0.75)
#ax.set_yscale('log')

ax.set_xlabel("ADC counts",fontsize=14)
#ax.set_ylabel("raw ADC counts", fontsize=14)

plt.show()
