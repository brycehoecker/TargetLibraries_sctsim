#/usr/bin/env python
# Colin Adams
# Created Feb 8 2016
# Based on J. Vandenbroucke's calibrateTF.py used with earlier driver
# Callibrate transfer function, as follows:
# Loop over Vped settings
# For each take a run.

# Import modules
import target
import time
import os
import recordModule
import configModuleT7

# Set up
sleepTime = 1
numAsics = 4
channelsPerAsic = 16

def calibrateTF(module, eventsPerRun, targetVersion):
	minVped = 125
	maxVped = 4061+1
	stepVped = 164

	# loop over Vped
	numSettings = 0
	VpedList = range(minVped,maxVped,stepVped)	#24 points
	for Vped in VpedList:
		# set Vped
		module.WriteSetting('Vped_value',Vped)
		numSettings += 1
		print "Finished setting Vped to %d counts." % Vped

		# Wait for Vped to settle
		print "Waiting %d sec for Vped to settle." % sleepTime
		time.sleep(sleepTime)

		# Take one run
		recordModule.recordModule(board,eventsPerRun,targetVersion)
		print "Finished %d of %d Vped values." % (numSettings,len(VpedList))

if __name__ == "__main__":
	
	# Set up
	eventsPerRun = 1
	targetVersion = 7
	
	# open connection to the module in some way or form
	module = configModuleT7.connect()	

	calibrateTF(module, eventsPerRun, targetVersion)
	
	# Close connection
	module.CloseSockets()
