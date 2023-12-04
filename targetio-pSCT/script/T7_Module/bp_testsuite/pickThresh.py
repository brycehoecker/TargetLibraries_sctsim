#!/usr/bin/env python

import os
import numpy as np
import glob
import math
import logging

def pickThresh(testDir="", testDirFinal="", freq=100,deadtime=12500, triggerEN=1):
	messedUpPick = 0
	homedir = os.environ['HOME']
	
	try:
		newest = max(glob.iglob('{}/test_suite/{}/triggerEfficiency_*'.format(homedir, testDir)), key=os.path.getctime)
	except:
		logging.warning("couldn't find directory: %s", testDir )
		try:
			newest = max(glob.iglob('{}/testRun_*/triggerEfficiency_*'.format(testDirFinal)), key=os.path.getctime)
		except:
			logging.warning("couldn't find directory: %s", testDirFinal )
			try:
				newest = max(glob.iglob('{}/oldTests/testRun_*/triggerEfficiency_*'.format(testDirFinal)), key=os.path.getctime)
			except:
				logging.warning("couldn't find sub directory: %s", testDirFinal )

	

	#indirname = '{}/target5and7data/triggerEfficiency/{}/'.format(homedir,dataset)
	indirname = '{}/{}/{}/'.format(newest,deadtime,triggerEN)
	#have to import the data here 
	filepaths = []
	for root, dirs, files in os.walk(indirname):
		for fi in files:
			filepaths.append(os.path.join(root,fi))
	filepaths = sorted(filepaths)
	listThreshRate = []
	for filepath in filepaths:
		threshRate = np.loadtxt(filepath,unpack=True)
		listThreshRate.append(threshRate)
	#finds a conservative thresh value at each pixel to use for waveform readout
	#conservative means only triggering on the flasher (no noise) 
	consThreshList = []
	aggrThreshList = []
	counter = 0
	hold=0
	for threshrate in listThreshRate:
		#create a thresh and rate array from file
		thresh = threshrate[0]
		rate = threshrate[1]
		asic = counter/4
		group = counter%4
	#	print("Starting asic {} group {}".format(asic,group))

		#finds out if values are in a range by creating list of booleans
		#used as a conditional for the elif
		cond1 = rate>freq-3
		cond2 = rate<freq+3
		cond3 = thresh<1500
		cond4 = rate==freq
		inRange = cond1*cond2*cond3
		inFreq = cond3*cond4
	#	print("inRange: {}".format(inRange))
		#if there is a trigger rate at the flasher freq
		
		if True in inFreq:
	#		print("freq {}, rate: {}".format(freq, rate))
			#create an array of booleans indicating the location of trigger rates at flasher freq
			justLED = (rate==freq)*(thresh<1800)
			#find the middle index of the trigger rates at flasher freq
	#		print("running asic {} group {}".format(asic,group))
	#		print("Just LED: {}".format(justLED) )
			consThreshIndex = int(math.ceil(np.median(np.where(justLED)[0])))
			#grab that thresh value
			consThresh = thresh[consThreshIndex]
			consThreshList.append(consThresh)
		
		#if there are trigger rates near the flasher freq 
		elif True in inRange:
	#		print("Jumped into inRange cycle?")			
			#find the middle index of that range of values
			consThreshIndex = int(math.ceil(np.median(np.where(inRange)[0])))
			#grab that thresh value
			consThresh = thresh[consThreshIndex]
			consThreshList.append(consThresh)

		#sometimes the rates all show up as 0 for a group
		else:
			messedUpPick = 1
			#need to turn this into a logging thing
			logging.warning("WARNING: asic {} group {} on the module does not have any trigger counts at the flasher frequency".format(asic,group))
			#fill in the spot with a placeholder value
			#try to replace it with a reasonable value from a different deadtime
			try:
				with open('{}/7500/1/a{}g{}.txt'.format(newest,asic,group)) as infile:
					thresh1, rate1 = np.loadtxt(infile, unpack=True)
					con1, con2, con3 = rate1 > freq-10, rate1 < freq+10, thresh1 < 1800
					inRange1 = con1*con2*con3
					consThreshIndex = int(math.ceil(np.median(np.where(inRange1)[0])))
					consThreshList.append(thresh[consThreshIndex])
					print "appended an untuned value for asic {} group {}".format(asic, group)
			#if a reasonable value doesn't exist yet, append a zero (equiv to high threshold)
			except:
				consThreshList.append(0)
				logging.warning("Threshpick failed, threshold set to maximum.");
		hold=0
		countRate=0
		for i in rate:
			if(hold==0 and i>105):
				aggrThreshList.append(thresh[countRate])
				hold=1
			countRate+=1

		counter += 1
	logging.info("Found conservative thresholds:")
	logging.info(consThreshList)
	logging.info("Found aggressive thresholds:")
	logging.info(aggrThreshList)

	return consThreshList, messedUpPick, aggrThreshList


if __name__ == "__main__":
	dataset = "20160815_1830"
	testDir = '/Users/colinadams/target5and7data/test_suite_output/FEE107FPM4.3'
	print pickThresh(testDir=testDir)




