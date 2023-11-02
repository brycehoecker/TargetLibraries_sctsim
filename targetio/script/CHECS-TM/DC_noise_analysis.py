import matplotlib
import numpy as np
import target_driver
import target_io

matplotlib.use('agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

directory = "/home/cta/luigi/CHECS-TM/data/20170425/DC_noise4/"
outfileroot = directory + "events_Vped{}.tio"
ped_vals = np.arange(1000, 4096, 50)

############################
# read waveforms and get ADC values in memory
Nevt = 1000  # number of events to use, must be <= number of events in file
NSamples = 128  # number of events to use, must be <= number of samples in wf
adc = np.zeros([len(ped_vals), Nevt, 4, 16, NSamples])
for s, vped in enumerate(ped_vals):
    # create the reader object
    reader = target_io.EventFileReader(outfileroot.format(vped))
    print "reading file", outfileroot.format(vped)
    NEvents = reader.GetNEvents()
    print "number of events", NEvents
    for ievt in range(Nevt):
        for asic in range(4):
            for channel in range(16):
                rawdata = reader.GetEventPacket(ievt, 16 * asic + channel)
                packet = target_driver.DataPacket()
                packet.Assign(rawdata, reader.GetPacketSize())
                wf = packet.GetWaveform(0)
                if wf.GetSamples() == NSamples:
                    adc[s, ievt, asic, channel, :] = wf.GetADCArray(NSamples)
                else:
                    adc[s, ievt, asic, channel, :] = adc[s, ievt-1, asic, channel, :]
                    #just a hack to do a quick plot

# now plot
# average ADC
for asic in range(4):
    fig = plt.figure('ASIC {}'.format(asic), (20., 8.))
    fig.suptitle("Asic {}".format(asic), fontsize=16, fontweight='bold',
                 bbox={'boxstyle': 'round4', 'facecolor': 'gray', 'alpha': 0.5})
    gs = gridspec.GridSpec(4, 4)
    gs.update(left=0.06, right=0.98, top=0.93, bottom=0.05, wspace=0.25, hspace=0.25)
    for channel in range(16):
        ax1 = plt.subplot(gs[channel / 4, channel % 4])
        ax1.set_xlabel('Vped DAC')
        ax1.set_ylabel('mean ADC counts')
        ax1.grid(True)
        plt.text(0.65, 0.9, " Channel {}".format(channel), transform=ax1.transAxes,
                 bbox={'boxstyle': 'roundtooth', 'facecolor': 'grey', 'alpha': 0.2})
        ax1.plot(ped_vals, np.average(adc[:, :, asic, channel, :], axis=(1, 2)))
    fig.savefig(directory + "meanADC_Asic{}.pdf".format(asic))
# RMS noise
for asic in range(4):
    fig = plt.figure('ASIC {}'.format(asic), (20., 8.))
    fig.suptitle("Asic {}".format(asic), fontsize=16, fontweight='bold',
                 bbox={'boxstyle': 'round4', 'facecolor': 'gray', 'alpha': 0.5})
    gs = gridspec.GridSpec(4, 4)
    gs.update(left=0.06, right=0.98, top=0.93, bottom=0.05, wspace=0.25, hspace=0.25)
    for channel in range(16):
        ax1 = plt.subplot(gs[channel / 4, channel % 4])
        ax1.set_xlabel('Vped DAC')
        ax1.set_ylabel('RMS noise (ADC counts, cell wise')
        ax1.grid(True)
        plt.text(0.65, 0.9, " Channel {}".format(channel), transform=ax1.transAxes,
                 bbox={'boxstyle': 'roundtooth', 'facecolor': 'grey', 'alpha': 0.2})
        rms_cell = np.std(adc[:, :, asic, channel, :], axis=1)
        ax1.plot(ped_vals, np.average(rms_cell, axis=1))
        if np.any(np.average(rms_cell, axis=1) > 5):
            print "large RMS noise, ASIC {}, Channel {}, Vped".format(asic, channel)
            print ped_vals[np.where(np.average(rms_cell, axis=1) > 5)]
    fig.savefig(directory + "RMSnoise_Asic{}.pdf".format(asic))
