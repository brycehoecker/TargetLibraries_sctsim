import time, os
import target_driver
import target_io

kNWavesPerPacket = 8
kNSamplesPerWave = 128

def SendDataPacket(simulator, packet, eventID, packetID):
    tack = eventID
    slotID = 0
    eventSequenceNumber = 0
    quad = 0
    row = 0
    col = 0

    tmp = packetID * kNWavesPerPacket
    detectorID = tmp / 64
    tmp %= 64
    asic = tmp / 16
    tmp %= 16;
    ch_offset = (tmp / kNWavesPerPacket) * kNWavesPerPacket

    packet.FillHeader(kNWavesPerPacket, kNSamplesPerWave, slotID, detectorID,
                      eventSequenceNumber, tack, quad, row, col);

    for i in range(kNWavesPerPacket):
        waveform = packet.GetWaveform(i)
        waveform.SetHeader(asic, ch_offset + i, kNSamplesPerWave, False)
        packet.FillFooter()	# zero out the last two footer words

    pid = 0
    ret, pid = packet.GetPacketID()

    simulator.SendDataPacket(packet.GetData(), packet.GetPacketSize())


if __name__ == "__main__":

    packet = target_driver.DataPacket(kNWavesPerPacket, kNSamplesPerWave)
    
    simulator = target_driver.ModuleSimulator("0.0.0.0")
    simulator.Start()

    # Some logic to load def files by finding them in user directories
    #TargetModule(FPGADef, ASICDef, TriggerASICDef, uint16_t);
    def1 = "/home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/config/SCT_MSA_FPGA_Firmware0xC000000E.def"
    def2 = "/home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/config/TC_ASIC.def"
    def3 = "/home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/config/T5TEA_ASIC.def"

    if os.path.exists(def1) and os.path.exists(def2) and os.path.exists(def3):
        # All three files exist
        print("All 3 Files exist.")
        module = target_driver.TargetModule(def1, def2, def3, 0)
    else:
        # At least one of the files does not exist
        print("One or more of the files does not exist.")
        module = target_driver.TargetModule(
            "/home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/config/SCT_MSA_FPGA_Firmware0xC000000E.def",
            "/home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/config/TC_ASIC.def", "/home/sctsim/git_repos/TargetLibraries_sctsim/targetdriver-pSCT/config/T5TEA_ASIC.def", 0)
    module.EstablishSlowControlLink("0.0.0.0", "0.0.0.0")

    kNPacketsPerEvent = 64
    kPacketSize = 2084
    kBufferDepth = 1000
    sleepTime = 0.01		# use this to throttle the readout rate
    numEvents = 10		# 3 or fewer gives segfault

    listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
    listener.AddDAQListener("0.0.0.0")
    listener.StartListening()

    # Remove the output file if it already exists
    filename = "testEventFile.fits"
    if os.path.exists(filename):
        os.remove(filename)
    writer = target_io.EventFileWriter(filename, kNPacketsPerEvent, kPacketSize)

    buf = listener.GetEventBuffer()
    writer.StartWatchingBuffer(buf)

    for eventID in range(numEvents):
        for packetID in range(kNPacketsPerEvent):
            SendDataPacket(simulator, packet, eventID, packetID)
        time.sleep(sleepTime)
        print ("Finished %d events." % (eventID + 1))

    buf.Flush()

    # Check if output file is valid fits file or not
    checkFits = True	# use this boolean to disable checking
    if checkFits:
        from astropy.io import fits
        try:
            hdulist = fits.open(filename)
        except IOError:
            print ('FITS file is invalid.')
        else:
            print ('FITS file is valid.')
    hdulist.close()
