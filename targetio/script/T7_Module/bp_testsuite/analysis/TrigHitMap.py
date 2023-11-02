import target_io
import target_driver
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec
import datetime
import time
import sys
import os
import run_control

# if 5x5 grid, True, if 4x4, False
full=0

# 4 asics, 16 ch per asic
nasic=4
nch=16

argList = sys.argv

runID=int(argList[1])

homedir = os.environ['HOME']
hostname = run_control.getHostName()
indirname = run_control.getDataDirname(hostname)
#print homedir, hostname, indirname, argList

filename = indirname+"	run{}.fits".format(runID)
print "Reading file: ", filename

"""
# modules need to be ordered in the same way that they were ordered in the data taking loop
modList=[118 ,125, 126, 101, 119, 108, 116, 110, 128, 123, 124, 112, 100, 111, 114, 107]
nModules = len(modList)

modPos = {119:17, 108:18, 116:19, 128:23, 123:24, 124:25, 
          112:26, 111:29, 114:30, 107:31, 118:11, 125:12,
	  126:13, 101:14, 110:20, 100:28}
posGrid =	{5:(1,1), 6:(1,2), 7:(1,3), 8:(1,4), 9:(1,5),
		11:(2,1), 12:(2,2), 13:(2,3), 14:(2,4), 15:(2,5),
		17:(3,1), 18:(3,2), 19:(3,3), 20:(3,4), 21:(3,5),
		23:(4,1), 24:(4,2), 25:(4,3), 26:(4,4), 27:(4,5), 
		28:(5,1), 29:(5,2), 30:(5,3), 31:(5,4), 32:(5,5)}


This method will calculate index reassignments 
that trace out the Z-order curve that the pixels 
form in the focal plane.
See: http://stackoverflow.com/questions/42473535/arrange-a-numpy-array-to-represent-physical-arrangement-with-2d-color-plot

def row_col_coords(index):
	# Convert bits 1, 3 and 5 to row
	row = 4*((index & 0b100000) > 0) + 2*((index & 0b1000) > 0) + 1*((index & 0b10) > 0)
	# Convert bits 0, 2 and 4 to col
	col = 4*((index & 0b10000) > 0) + 2*((index & 0b100) > 0) + 1*((index & 0b1) > 0)
	return (row, col)

# calculating the actual index reassignments
row, col = row_col_coords(np.arange(64))

# set up reader, find number of events, packet size, and number of samples 
reader = target_io.EventFileReader(filename)
nEvents = reader.GetNEvents()
print "number of events", nEvents
if nEvents > 500:
	nEvents = 200
rawdata = reader.GetEventPacket(0,0)
packet = target_driver.DataPacket()
packet.Assign(rawdata, reader.GetPacketSize())
print "The Packet size is: ", reader.GetPacketSize()
wf = packet.GetWaveform(0)
nSamples = wf.GetSamples()
print "Number of samples: ", wf.GetSamples()

ampl = np.zeros([nEvents,nModules,nasic,nch,nSamples])
heatArray = np.zeros([nModules,nasic, nch])
baseArray = np.zeros([nModules,nasic, nch])
timeArray = np.zeros([nModules,nasic, nch])
rmsArray = np.zeros([nModules,nasic, nch])
physHeatArr = np.zeros([nModules,8,8])
physBaseArr = np.zeros([nModules,8,8])
physTimeArr = np.zeros([nModules,8,8])
physRMSArr = np.zeros([nModules,8,8])

# set up plotting
heatFig = plt.figure('Pixel Heat Map', (18.,15.))
baseFig = plt.figure('Baseline Heat Map', (18.,15.))
timeFig = plt.figure('Peak Time Map', (18.,15.))
rmsFig = plt.figure('Baseline RMS Map', (18.,15.))

if full:
	gs = gridspec.GridSpec(5,5)
else:
	gs = gridspec.GridSpec(4,4)
gs.update(wspace=0.04, hspace=0.04)

for modInd in range(len(modList)):	
	for asic in range(nasic):
		for ch in range(nch):
			for ievt in range(nEvents):
				# eight channels stored in one packet
				# only grabbing first event
				rawdata = reader.GetEventPacket(ievt, (4*modInd+asic)*(nch/8)+(ch/8))
				packet = target_driver.DataPacket()
				packet.Assign(rawdata, reader.GetPacketSize())
				header = target_driver.EventHeader()
				reader.GetEventHeader(ievt, header);
				wf = packet.GetWaveform(ch%8)
				for sample in range(nSamples):
					ampl[ievt, modInd, asic, ch, sample] = wf.GetADC(sample)
				# avg the first 20 samples
				baseline=np.average(ampl[ievt,modInd,asic,ch,1:20])
				# get std dev of baseline
				stddev = np.std(ampl[ievt,modInd,asic,ch,1:20])
				# find the max of the waveform
				maxADC=ampl[ievt,modInd,asic,ch,35:].max()
				maxLoc=np.where(ampl[ievt,modInd,asic,ch,35:]==maxADC)[0][0]+35
				# append the subtraction to a pixel array
				heatArray[modInd,asic,ch]+=maxADC-baseline
				baseArray[modInd,asic,ch]+=baseline
				timeArray[modInd,asic,ch]+=maxLoc
				rmsArray[modInd,asic,ch]+=stddev

# reshapes the heatArray from (len(modList),4,16) to (len(modList),64)
# this allows us to use the index reassignment function
# also taking the average of the heat array
heatArray = heatArray.reshape((len(modList),64))*1./nEvents
baseArray = baseArray.reshape((len(modList),64))*1./nEvents
timeArray = timeArray.reshape((len(modList),64))*1./nEvents
rmsArray = rmsArray.reshape((len(modList),64))*1./nEvents

# apply index reassignment
# phys array will appear upside down in array form
# but pcolor plots index 0 from bottom up
physHeatArr[:,row,col] = heatArray
physBaseArr[:,row,col] = baseArray
physTimeArr[:,row,col] = timeArray
physRMSArr[:,row,col] = rmsArray

for modInd in range(len(modList)):
	# determine the location of the module in the gridspace
	if full:
		loc = tuple(np.subtract(posGrid[modPos[modList[modInd]]],(1,1)))
	else:
		loc = tuple(np.subtract(posGrid[modPos[modList[modInd]]],(2,1)))
	# modules in odd columns are rotated by 180 degrees
	# these are even columns here, because gridspec uses 0-based indexing
	if loc[1]%2==0:
		physHeatArr[modInd,:,:]=np.rot90(physHeatArr[modInd,:,:],k=2)
		physBaseArr[modInd,:,:]=np.rot90(physBaseArr[modInd,:,:],k=2)
		physTimeArr[modInd,:,:]=np.rot90(physTimeArr[modInd,:,:],k=2)
		physRMSArr[modInd,:,:]=np.rot90(physRMSArr[modInd,:,:],k=2)
	# deal with heat map
	plt.figure('Pixel Heat Map')
	ax = plt.subplot(gs[loc])
	c = ax.pcolor(physHeatArr[modInd,:,:], vmin=0, vmax=1500)
	# take off axes	
	ax.axis('off')
	ax.set_aspect('equal')

	# deal with baseline map
	plt.figure('Baseline Heat Map')
	ax1 = plt.subplot(gs[loc])
	c1 = ax1.pcolor(physBaseArr[modInd,:,:], vmin=0, vmax=1000)
	# take off axes	
	ax1.axis('off')
	ax1.set_aspect('equal')
	
	# deal with time map
	plt.figure('Peak Time Map')
	ax2 = plt.subplot(gs[loc])
	c2 = ax2.pcolor(physTimeArr[modInd,:,:], vmin=35, vmax=63)
	# take off axes	
	ax2.axis('off')
	ax2.set_aspect('equal')

	# deal with time map
	plt.figure('Baseline RMS Map')
	ax3 = plt.subplot(gs[loc])
	c3 = ax3.pcolor(physRMSArr[modInd,:,:], vmin=0, vmax=100)
	# take off axes	
	ax3.axis('off')
	ax3.set_aspect('equal')

savedir = "{}/Pictures/testpxl".format(homedir)

heatFig.subplots_adjust(right=0.8,top=0.9,bottom=0.1)
cbar_ax = heatFig.add_axes([0.85, 0.15, 0.05, 0.7])
cbar = heatFig.colorbar(c, cax=cbar_ax)
cbar.set_label('Max ADC - baseline (ADC counts)', rotation=270,size=20,labelpad=24)
cbar_ax.tick_params(labelsize=16)
heatFig.savefig("{}/{}_pxlHeatMap.png".format(savedir,runID))

baseFig.subplots_adjust(right=0.8,top=0.9,bottom=0.1)
cbar_ax1 = baseFig.add_axes([0.85, 0.15, 0.05, 0.7])
cbar1 = baseFig.colorbar(c1, cax=cbar_ax1)
cbar1.set_label('Baseline (ADC Counts)', rotation=270,size=20,labelpad=24)
cbar_ax1.tick_params(labelsize=16)
baseFig.savefig("{}/{}_pxlBaseMap.png".format(savedir,runID))

timeFig.subplots_adjust(right=0.8,top=0.9,bottom=0.1)
cbar_ax2 = timeFig.add_axes([0.85, 0.15, 0.05, 0.7])
cbar2 = timeFig.colorbar(c2, cax=cbar_ax2)
cbar2.set_label('Time of peak ADC count (ns)', rotation=270,size=20,labelpad=24)
cbar_ax2.tick_params(labelsize=16)
timeFig.savefig("{}/{}_pxlPeakTimeMap.png".format(savedir,runID))

rmsFig.subplots_adjust(right=0.8,top=0.9,bottom=0.1)
cbar_ax3 = rmsFig.add_axes([0.85, 0.15, 0.05, 0.7])
cbar3 = rmsFig.colorbar(c3, cax=cbar_ax3)
cbar3.set_label('Baseline RMS (ADC counts)', rotation=270,size=20,labelpad=24)
cbar_ax3.tick_params(labelsize=16)
rmsFig.savefig("{}/{}_pxlRMSbaselineMap.png".format(savedir,runID))
"""
