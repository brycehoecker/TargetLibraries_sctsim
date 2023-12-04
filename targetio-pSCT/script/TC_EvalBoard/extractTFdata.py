import target_io
import target_driver
import numpy as np

#Vped_DAC = np.arange(495,4096,2)
#Vped_DAC = np.arange(495,499,2)
#Vped_DAC = np.arange(495,4096,120)
Vped_DAC = np.arange(495,4096,1)

datadir="/home/cta/luigi/TC_EvalBoard/data/20160307/1VpedDAC_SBias1050/"

nsample=96
nevent=200#max number of events read

tf_array=np.zeros([len(Vped_DAC),nsample,nevent])

for s, Vped in enumerate(Vped_DAC):
    ampl = np.zeros([nsample,nevent])
    #print "processing TF data for Vped {} DAC counts".format(Vped)
    filename=datadir+"TFdata_VpedDAC_{:04d}.fits".format(Vped)
    reader = target_io.EventFileReader(filename)
    #print "done"
    for ievt in range(nevent):
        rawdata = reader.GetEventPacket(ievt,0)#second entry is asic/channel, only one enabled in this case
        packet = target_driver.DataPacket()
        packet.Assign(rawdata, reader.GetPacketSize())
        wf = packet.GetWaveform(0)
        for sample in range(nsample):
            ampl[sample,ievt] = wf.GetADC(sample+12)
    tf_array[s,:,:]= ampl[:,:]

np.savez_compressed(datadir+"TFdata.npz",tf_array,Vped_DAC)