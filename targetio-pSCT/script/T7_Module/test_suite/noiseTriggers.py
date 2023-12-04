import target_io
import target_driver
import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec
import datetime
import time
import sys
import os
import run_control

def getNoiseRuns(runsFile):
	noiseRunList = []
	grabNext=0
	runsFile.seek(0,0)
	for line in runsFile:
		if grabNext == 0:
			if line.split()[0]=="Noise" and line.split()[2]=="internal" and line.split()[-1].isdigit():
				grabNext = 1
			else:
				grabNext = 0
		else:
			noiseRunList.append(int(line))
			grabNext = 0
	return noiseRunList

def plotNoiseTriggers(runList, testDir, dataset):
	eventList = []
	for runID in runList:
		indirname = testDir
		filename = indirname+"/run{}.fits".format(runID)
		reader = target_io.EventFileReader(filename)
		nEvents = reader.GetNEvents()
		print "number of events", nEvents
		eventList.append(nEvents)

	eventList = np.asarray(eventList)
	#print eventList
	groups = np.arange(16)
	#print groups
	
	fig, ax1 = plt.subplots()
	ax1.plot(groups,eventList,'ro')
	ax1.set_title('Triggers per enabled group in 10 s')
	ax1.set_xlabel('Group w/ trigger enabled')
	ax1.set_ylabel('# of triggers counted in 10 s')
	fig.savefig('{}/internalNoiseTriggers_{}'.format(testDir,dataset))
	#plt.show()

if __name__ == "__main__":
	filename = "/Users/colinadams/target5and7data/test_suite_output/FEE111FPM4.1/oldTests/testRun_20161024_1608/associatedRuns_20161024_1608.log"
	inFile = open(filename,'a+')
	noiseRunList = getNoiseRuns(inFile)
	testDir = "/Users/colinadams/target5and7data"
	plotNoiseTriggers(noiseRunList, testDir, dataset="20161024_1608")
