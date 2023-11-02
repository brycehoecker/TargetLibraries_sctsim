import target_io
import target_driver
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec
import time
import datetime

now = datetime.datetime.now()
outdirname = now.strftime("%m%d%y")
specname = now.strftime("%H%M%S")


FirstRun = 293114
LastRun = 293117

#LastRun = FirstRun

#runList = np.linspace(286686,286810,125)
#runList = [286684,286685]
#runList = np.linspace(286836,286860,25)
#runList = [286891,286892,286893,286894,286895]

#runList = range(286906,286980+1)
#runList = range(286981,287055+1)
#runList = range(287056,287080+1)
#runList = range(286956,286980+1)
#runList = range(287081,287105+1)
#runList = range(287106,287130+1)
runList = range(FirstRun,LastRun+1)

#runList = np.concatenate([range(287290,287314+1),range(287265,287289+1),range(287132,287156+1)])


count = 1

nEventList = []

for runID in runList:

	filename = "/Users/twu58/target5and7data/run%d.fits" % (runID)
	#filename = "/Volumes/RAMDISK/temp/run%d.fits" % (runID)
	nSamples = 14*32
	nchannel = 16
	nasic = 4

	reader = target_io.EventFileReader(filename)
	nEvents = reader.GetNEvents()
	print count, "number of events", nEvents
	nEventList.append(nEvents)
	count = count+1
	if count == 11:
		count = 1

fig = plt.plot(range(1,np.size(runList)+1),nEventList,marker='o')
plt.title("numEvent plot Run%dtoRun%d" % (FirstRun,LastRun))
#plt.title("numEvent plot")
plt.xlabel('run number')
plt.ylabel('number of events')
#plt.ylim([0,3500])

print nEventList

plt.savefig('/Users/twu58/Pictures/%s/numEventPlotRun%dtoRun%d.png' % (outdirname,FirstRun,LastRun) )
