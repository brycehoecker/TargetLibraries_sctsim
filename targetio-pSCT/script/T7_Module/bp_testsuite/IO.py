import target_driver
import target_io
import time

"""Initialize the data listening and writing"""
def setUp(my_ip, kBufferDepth, kNPacketsPerEvent, kPacketSize, outFile):


	listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
	print "The used ip is: ", my_ip
	print "The used buffer depth:", kBufferDepth
	print "The used packets per event:", kNPacketsPerEvent
	print "The used packetsize:", kPacketSize

        listener.AddDAQListener(my_ip)
        listener.StartListening()

        writer = target_io.EventFileWriter(outFile, kNPacketsPerEvent, kPacketSize)
        buf = listener.GetEventBuffer()
	return buf, writer, listener

"""Write data with the writer for a specific duration of time"""
def takeData(writer, buf, runDuration):
	writer.StartWatchingBuffer(buf)
	time.sleep(runDuration)
	writer.StopWatchingBuffer()

"""Stop the data listener and close writer""" 
def stopData(listener, writer):
	listener.StopListening()
	writer.Close()
