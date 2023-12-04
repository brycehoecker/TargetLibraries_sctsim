import target_io
import target_driver
import numpy as np
import matplotlib.pyplot as plt
import evaluateTF
import gc

datadir1="/home/cta/luigi/TC_EvalBoard/data/20160705/testTF/"
# parname = "Isel"
# parvals = np.arange(2280, 2300, 10)
# parname = 'SBbias'
# parvals = np.arange(1900,2010,10)
# parname = 'PUbias'
# parvals = np.arange(3000,3200,10)
# parname = "Isel"
# parvals = np.arange(2290, 2302, 2)
# parname = "CMPbias"
# parvals = np.arange(1600,1710,10)
# parname = "Isel"
# parvals = np.arange(2300, 2320, 10)
# parname = "CMPbias2"
# parvals = np.arange(300,1000,100)
# parname = 'SBbias'
# parvals = np.arange(1920,1941,1)
# parname = 'PUbias'
# parvals = np.arange(3010,3034,2)
# parname = "Isel"
# parvals = np.arange(2290, 2312, 2)
# parname = "CMPbias"
# parvals = np.arange(1610,1631,1)
# parname = "Isel"
# parvals = np.arange(2298, 2302, 2)
# parname = "CMPbias2"
# parvals = np.arange(710,731,1)
parname = "Isel"
parvals = np.arange(2300, 2301, 1)

Vped_DAC = np.arange(495,4096,120)
nsample=64
nevent=300

drange = np.zeros(len(parvals))
INL = np.zeros(len(parvals))
avdcnoise = np.zeros(len(parvals))
eff_drange = np.zeros(len(parvals))
dcnoise_lower = np.zeros(len(parvals))

outfile = open(datadir1+"results.txt","w")
outfile.write(parname+" dynamic range (mV) INL (ADC counts) DC noise (mV) efective dynamic range (bits) \n")

for ipar, parval in enumerate(parvals):
    datadir = datadir1+'{}_{:04d}/'.format(parname,parval)
    print "processing data in", datadir
    tf_array=np.zeros([len(Vped_DAC),nsample,nevent])
    #extract values and save to np array
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
        reader.Close()
    np.savez_compressed(datadir+"TFdata.npz",tf_array,Vped_DAC)
    #evaluate TF
    tf = evaluateTF.TargetTF(datadir+"TFdata.npz")
    #tf.plot_TF(outdir=datadir)
    drange1, INL1, avdcnoise1, eff_drange1, dcnoise_lower1 = tf.evaluate(datadir,npoint=2, noise_cut=2,lindev_cut=400)
    drange[ipar]  = drange1
    INL[ipar] = INL1
    avdcnoise[ipar] = avdcnoise1
    eff_drange[ipar] = eff_drange1
    dcnoise_lower[ipar] = dcnoise_lower1
    outfile.write("{} {} {} {} {}\n".format(parval,drange1,INL1,avdcnoise1,eff_drange1,dcnoise_lower1))
    del tf
    gc.collect()

outfile.close()

#now plot
fig = plt.figure("Dynamic Range")
ax = plt.subplot(111)
ax.set_xlabel(parname, fontsize=14)
ax.set_ylabel("dynamic range (mV)", fontsize=14)
ax.plot(parvals,drange,marker='o',linewidth=0,color='k')
fig.savefig(datadir1+"drange.png")

fig = plt.figure("DC Noise")
ax = plt.subplot(111)
ax.set_xlabel(parname, fontsize=14)
ax.set_ylabel("DC noise (mV)", fontsize=14)
ax.set_ylim(0,4)
ax.plot(parvals,avdcnoise,marker='o',linewidth=0,color='k')
fig.savefig(datadir1+"dcnoise.png")

fig = plt.figure("INL")
ax = plt.subplot(111)
ax.set_xlabel(parname, fontsize=14)
ax.set_ylabel("Integrated Non Linearity (ADC counts)", fontsize=14)
ax.plot(parvals,INL,marker='o',linewidth=0,color='k')
fig.savefig(datadir1+"inl.png")

fig = plt.figure("Effective Dynamic Range")
ax = plt.subplot(111)
ax.set_xlabel(parname, fontsize=14)
ax.set_ylabel("effective dynamic range (bit)", fontsize=14)
ax.plot(parvals,eff_drange,marker='o',linewidth=0,color='k')
fig.savefig(datadir1+"effdrane.png")

fig = plt.figure("DC noise lower")
ax = plt.subplot(111)
ax.set_xlabel(parname, fontsize=14)
ax.set_ylabel("DC noise at lower end of dyn. range (mV)", fontsize=14)
ax.plot(parvals,dcnoise_lower,marker='o',linewidth=0,color='k')
fig.savefig(datadir1+"dcnoiselower.png")
