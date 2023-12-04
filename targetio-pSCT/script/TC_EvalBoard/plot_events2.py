import target_driver
import target_io
import matplotlib.pyplot as plt
import numpy as np
import pdb
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--filename", help="Name of input file", type=str, default="test.fits")
parser.add_argument("-d" ,"--directory", help="Output directory", type=str, default="./")
parser.add_argument("-N" ,"--Nevents", help="Number of events to be displayed. 0 will show all events in the file", type=int, default="0")
parser.add_argument("-c" ,"--channel", help="Channel to be displayed", type=int, default="0")
args = parser.parse_args()

#filename = "/home/cta/luigi/TC_EvalBoard/20160729/hardsync/DelayScan/DelayScanevents_dly00224.fits"
#filename = "/home/cta/luigi/TC_EvalBoard/20160729/internal/test57.fits"
filename=args.directory+"/"+args.filename

Nsamples = 4*32
sample0=0
channel=args.channel 

reader = target_io.EventFileReader(filename)

NEvents  = reader.GetNEvents()

print NEvents, "events read"

ampl = np.zeros([NEvents,Nsamples])
ax = plt.subplot(111)
ax.set_xlabel("sample",fontsize=14)
ax.set_ylabel("raw ADC counts", fontsize=14)
ax.set_title("Channel "+str(channel))

nevt = args.Nevents
if nevt==0:
    nevt=NEvents

for ievt in range(nevt):
    rawdata = reader.GetEventPacket(ievt,channel)#second entry is asic/channel, only one enabled in this case
    packet = target_driver.DataPacket()
    packet.Assign(rawdata, reader.GetPacketSize())
    wf = packet.GetWaveform(0)
    for sample in range(Nsamples):
        ampl[ievt,sample] = wf.GetADC(sample0+sample)
    ax.plot(ampl[ievt],alpha=0.7)




plt.show()



