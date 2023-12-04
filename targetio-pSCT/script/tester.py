#!/usr/bin/env python
# Justin Vandenbroucke
# Created Jun 23 2016
# Test TargetIO with a simulated TARGET module.
# Based on tutorial.py.

# Import modules
import os, sys, time
import target_driver
import target_io
from tutorial import SendDataPacket

# User selected variables
kNumModules = 1							# e.g. 1 for single module, 32 for GCT, 16 for pSCT
kNChannelsPerPacket = 64					# number of channels per packet; GCT uses 8
kNBlocksPerEvent = 2						# e.g. 2 for pSCT, 4 for GCT
kBufferDepth = 1000						# measured in bytes or events?
numEvents = 1000						# 3 or fewer gives segfault
checkFits = False						# use this boolean to disable checking validity of fits file (e.g. if astropy not installed)

# Constants
kNSamplesPerBlock = 32
kChannelsPerModule = 64
kAdditionalHeaderWords = 10
kBytesPerWord = 2
kNWordsForChannelID = 1
bytesPerMB = 1.0e6

# Derived quantities
kTotalNumChannels = kNumModules * kChannelsPerModule
kNSamplesPerWave = kNBlocksPerEvent * kNSamplesPerBlock		# number of samples per event per channel; GCT uses 128
kNPacketsPerEvent = kTotalNumChannels/kNChannelsPerPacket	# kNPacketsPerEvent * kNChannelPerPacket is the total number of channels (2048 for GCT)
kPacketSize = (kNChannelsPerPacket*(kNBlocksPerEvent*kNSamplesPerBlock+kNWordsForChannelID) + kAdditionalHeaderWords) * kBytesPerWord
kEventSize = kPacketSize*kNPacketsPerEvent
sizeNeeded = kEventSize*numEvents

print "There are %d packets per event." % kNPacketsPerEvent
print "Total file size will be %.2f MB." % (sizeNeeded/bytesPerMB)

def SendDataPacket(simulator, packet, eventID, packetID):
    tack = eventID
    slotID = 0
    eventSequenceNumber = 0
    quad = 0
    row = 0
    col = 0

    tmp = packetID * kNChannelsPerPacket
    detectorID = tmp / 64
    tmp %= 64
    asic = tmp / 16
    tmp %= 16;
    ch_offset = (tmp / kNChannelsPerPacket) * kNChannelsPerPacket

    packet.FillHeader(kNChannelsPerPacket, kNSamplesPerWave, slotID, detectorID,
                      eventSequenceNumber, tack, quad, row, col);
    packet.FillFooter()	# zero out the last two footer words

    for i in range(kNChannelsPerPacket):
        waveform = packet.GetWaveform(i)
        waveform.SetHeader(asic, ch_offset + i, kNSamplesPerWave, False)

    pid = 0
    ret, pid = packet.GetPacketID()

    simulator.SendDataPacket(packet.GetData(), packet.GetPacketSize())

if __name__ == "__main__":

    packet = target_driver.DataPacket(kNChannelsPerPacket, kNSamplesPerWave)
    
    simulator = target_driver.ModuleSimulator("0.0.0.0")
    simulator.Start()

    # Load def files
    def1 = "/Users/justin/Dropbox/TargetDriver/config/TM5_FPGA_Firmware0xFEDA003C.def"
    def2 = "/Users/justin/Dropbox/TargetDriver/config/TM5_ASIC.def"
    module = target_driver.TargetModule(def1, def2, 0)
    module.EstablishSlowControlLink("0.0.0.0", "0.0.0.0")
    print "Established slow control link."

    listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
    listener.AddDAQListener("0.0.0.0")
    listener.StartListening()

    # Remove the output file if it already exists
    filename = "tester.fits"
    if os.path.exists(filename):
	os.remove(filename)
    writer = target_io.EventFileWriter(filename, kNPacketsPerEvent, kPacketSize)

    buf = listener.GetEventBuffer()
    writer.StartWatchingBuffer(buf)
#    buf.Flush()

    print "Finished setting up.  Will now record events."

    startTime = time.time()
    for eventID in range(numEvents):
        for packetID in range(kNPacketsPerEvent):
            packetSize = SendDataPacket(simulator, packet, eventID, packetID)
	if not ((eventID+1)%100):
        	print "Finished %d events." % (eventID + 1)
	#time.sleep(0.01)

    stopTime = time.time()
    elapsedTime = stopTime - startTime
    eventRate = numEvents/elapsedTime
    print "%.2f MB written in %.2f sec (%.2f kHz = %.2f MB/sec = %.2f Mbps)." % (sizeNeeded/bytesPerMB, eventRate/1e3,elapsedTime,sizeNeeded/elapsedTime/bytesPerMB,8*sizeNeeded/elapsedTime/bytesPerMB)
    buf.Flush()

    # Check if output file is valid fits file or not
    if checkFits:
        from astropy.io import fits
        try:
            hdulist = fits.open(filename)
        except IOError:
            print 'FITS file is invalid.'
        else:
            print 'FITS file is valid.'
	    hdulist.close()
