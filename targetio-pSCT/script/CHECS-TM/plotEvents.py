import matplotlib.pyplot as plt
import numpy as np
import target_driver
import target_io

####parameters to change####
filename = "/home/cta/luigi/CHECS-TM/data/20170502/test/test37.fits"
#filename = "/home/cta/luigi/CHECS-TM/data/20170502/trigdelay_scan3/events_dly0512.tio"
channel = 40
############################

# create the reader object
reader = target_io.EventFileReader(filename)
NEvents = reader.GetNEvents()
print "number of events", NEvents

# create the plot
ax = plt.subplot(111)
ax.set_xlabel("sample", fontsize=14)
ax.set_ylabel("raw ADC counts", fontsize=14)
ax.set_title("Channel " + str(channel))

imin = 10
for ievt in range(imin,30):
    rawdata = reader.GetEventPacket(ievt, channel)  # second entry is 16*asic+channel
    packet = target_driver.DataPacket()
    packet.Assign(rawdata, reader.GetPacketSize())
    wf = packet.GetWaveform(0)
    if ievt == imin:
        NSamples = wf.GetSamples()
        adc = np.zeros([NEvents, NSamples], dtype=np.uint16)
        print "number of samples per waveform", NSamples
    adc[ievt] = wf.GetADCArray(NSamples)
    ax.plot(adc[ievt], alpha=0.7)

plt.show()
