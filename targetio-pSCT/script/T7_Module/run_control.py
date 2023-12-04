# Justin Vandenbroucke
# Created Apr 27 2013
# Handle run numbering.
# Automatically keep track of most recent run number and increment it.
# Uses a simple text file method

import os
import socket

def incrementRunNumber(outdirname):
	# Handle automatic run number incrementing using a local text file
	#dirname = os.getenv('TARGET_DATA')
	runFilename = '%s/previousRun.txt' % outdirname
	#runFilename = '/Users/twu58/previousRun.txt'
	file = open(runFilename,'r')
	previousRun = int(file.read())
	file.close()
	runID = previousRun + 1
	runString = "%d" % runID
	file = open(runFilename,'w')
	file.write(runString)
	file.close()
	print "Starting Run %d." % runID
	return runID

def getHostName():
	name = socket.gethostname()
	print "Host name is %s." % name
	return name

def getDataDirname(hostname):
	homedir = os.environ['HOME']
	outdirname = '%s/target5and7data/' % homedir

	if os.path.exists(outdirname):
		print "Ready for writing to %s" % outdirname
	else:
		print "ERROR in getDataDirname(): output directory does not exist: %s." % outdirname
		sys.exit(1)
	return outdirname
