import datetime
import shutil
import glob
import target_driver
import sys



def logRegister(module, outdirname, runID):

	logfilename = "%s/run%d.log" % (outdirname,runID)
	logfile = open(logfilename,'w')

	for addr in range(129):
		value = module.ReadRegister(addr)
		hexValue = "0x%08x" % value[1]
		hexAddress = "0x%02x" % addr
		currentTime = datetime.datetime.utcnow()
		line = "%s\t%s\t%s\n" % (currentTime, hexAddress, hexValue)
		logfile.write(line)


###	module.QueryAndPrintAllRegisters( logfile)


	logfile.close()
	print "%s written." % (logfilename)
	return 0;

