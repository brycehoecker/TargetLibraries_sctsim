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
import h5py
from sct_toolkit import pedestal, waveform

# if 5x5 grid, True, if 4x4, False
full=0

# switch to 1 to produce a movie
movie=1

# 4 asics, 16 ch per asic
nasic=4
nch=16

argList = sys.argv

singleEvent = 0
eventNum = 0

runID=int(argList[1])

homedir = os.environ['HOME']
#hostname = run_control.getHostName()
#indirname = run_control.getDataDirname(hostname)

#filename = indirname+"run{}.fits".format(runID)
filename = "/home/ctauser/runFiles/run{}.h5".format(runID)
print "Reading file: ", filename
wf = waveform(filename)

# modules need to be ordered in the same way that they were ordered in the data taking loop
modList=[118,125,126,119,108,121,110,128,123,124,112,100,111,114,107]
nModules = len(modList)

modPos = {119:17, 108:18, 121:19, 128:23, 123:24, 124:25, 
          112:26, 111:29, 114:30, 107:31, 118:11, 125:12,
	  126:13, 101:14, 110:20, 100:28}
posGrid =	{5:(1,1), 6:(1,2), 7:(1,3), 8:(1,4), 9:(1,5),
		11:(2,1), 12:(2,2), 13:(2,3), 14:(2,4), 15:(2,5),
		17:(3,1), 18:(3,2), 19:(3,3), 20:(3,4), 21:(3,5),
		23:(4,1), 24:(4,2), 25:(4,3), 26:(4,4), 27:(4,5), 
		28:(5,1), 29:(5,2), 30:(5,3), 31:(5,4), 32:(5,5)}

"""
This method will calculate index reassignments 
that trace out the Z-order curve that the pixels 
form in the focal plane.
See: http://stackoverflow.com/questions/42473535/arrange-a-numpy-array-to-represent-physical-arrangement-with-2d-color-plot
"""
def row_col_coords(index):
	# Convert bits 1, 3 and 5 to row
	row = 4*((index & 0b100000) > 0) + 2*((index & 0b1000) > 0) + 1*((index & 0b10) > 0)
	# Convert bits 0, 2 and 4 to col
	col = 4*((index & 0b10000) > 0) + 2*((index & 0b100) > 0) + 1*((index & 0b1) > 0)
	return (row, col)

# calculating the actual index reassignments
row, col = row_col_coords(np.arange(64))

get_dimensions = np.array(wf.get_branch('Module{}/Asic0/Channel0/cal_waveform'.format(modList[0])))
nEvents, nSamples = get_dimensions.shape

ampl = np.zeros([nModules,nasic,nch,nEvents,nSamples])
charge = np.zeros([nModules,nasic,nch,nEvents])
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
heatReflectFig = plt.figure('Heat Map Skyview', (18.,15.))
#baseFig = plt.figure('Baseline Heat Map', (18.,15.))
#timeFig = plt.figure('Peak Time Map', (18.,15.))
#rmsFig = plt.figure('Baseline RMS Map', (18.,15.))

if full:
	gs = gridspec.GridSpec(5,5)
else:
	gs = gridspec.GridSpec(4,4)
gs.update(wspace=0.04, hspace=0.04)

for modInd, modNum in enumerate(modList):	
	for asic in range(nasic):
		for ch in range(nch):
			cal_samples = np.array(wf.get_branch('Module{}/Asic{}/Channel{}/cal_waveform'.format(modNum,asic,ch)))
			ampl[modInd, asic, ch] = cal_samples
			charges_allEvts = np.array(wf.get_branch('Module{}/Asic{}/Channel{}/charge'.format(modNum,asic,ch)))
			charge[modInd, asic, ch] = charges_allEvts

if singleEvent:
	print "Selecting single event {}".format(eventNum)
	reduced_ampl = ampl[:,:,:,eventNum]
	reduced_charge = charge[:,:,:,eventNum]
	print reduced_ampl.shape
else:
	print "Averaging events"
	reduced_ampl = np.mean(ampl, axis=3)
	reduced_charge = np.mean(charge,axis=3)
	print reduced_ampl.shape

"""
for modInd, modNum in enumerate(modList):
        for asic in range(nasic):
                for ch in range(nch):
			maxLoc=np.argmax(reduced_ampl[modInd,asic,ch])
			#integrate_window=np.sum(reduced_ampl[modInd,asic,ch,maxLoc-4:maxLoc+8])
			heatArray[modInd,asic,ch]=integrate_window
"""

heatArray=reduced_charge
# reshapes the heatArray from (len(modList),4,16) to (len(modList),64)
# this allows us to use the index reassignment function
heatArray = heatArray.reshape((len(modList),64))
#baseArray = baseArray.reshape((len(modList),64))
#timeArray = timeArray.reshape((len(modList),64))
#rmsArray = rmsArray.reshape((len(modList),64))

# apply index reassignment
# phys array will appear upside down in array form
# but pcolor plots index 0 from bottom up
physHeatArr[:,row,col] = heatArray
#physBaseArr[:,row,col] = baseArray
#physTimeArr[:,row,col] = timeArray
#physRMSArr[:,row,col] = rmsArray

for modInd in range(len(modList)):
	# determine the location of the module in the gridspace
	if full:
		reflectList = [4, 3, 2, 1, 0]
		loc = tuple(np.subtract(posGrid[modPos[modList[modInd]]],(1,1)))
		locReflect = tuple([loc[0],reflectList[loc[1]]])
	else:
		reflectList = [3, 2, 1, 0]
		loc = tuple(np.subtract(posGrid[modPos[modList[modInd]]],(2,1)))
		locReflect = tuple([loc[0],reflectList[loc[1]]])
	# modules in odd columns are rotated by 180 degrees
	# these are even columns here, because gridspec uses 0-based indexing
	if loc[1]%2==0:
		physHeatArr[modInd,:,:]=np.rot90(physHeatArr[modInd,:,:],k=2)
#		physBaseArr[modInd,:,:]=np.rot90(physBaseArr[modInd,:,:],k=2)
#		physTimeArr[modInd,:,:]=np.rot90(physTimeArr[modInd,:,:],k=2)
#		physRMSArr[modInd,:,:]=np.rot90(physRMSArr[modInd,:,:],k=2)
	# deal with heat map
	plt.figure('Pixel Heat Map')
	ax = plt.subplot(gs[loc])
	c = ax.pcolor(physHeatArr[modInd,:,:], vmin=0, vmax=7000)
	# take off axes	
	ax.axis('off')
	ax.set_aspect('equal')

        # deal with skyview heat map
        plt.figure('Heat Map Skyview')
        ax4= plt.subplot(gs[locReflect])
        c4 = ax4.pcolor(physHeatArr[modInd,:,::-1], vmin=0, vmax=7000)
        # take off axes
        ax4.axis('off')
        ax4.set_aspect('equal')

	"""
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
	"""

savedir = "{}/Pictures/testpxl".format(homedir)

heatFig.subplots_adjust(right=0.8,top=0.9,bottom=0.1)
cbar_ax = heatFig.add_axes([0.85, 0.15, 0.05, 0.7])
cbar = heatFig.colorbar(c, cax=cbar_ax)
cbar.set_label('Charge', rotation=270,size=20,labelpad=24)
cbar_ax.tick_params(labelsize=16)

heatReflectFig.subplots_adjust(right=0.8,top=0.9,bottom=0.1)
cbar_ax4 = heatReflectFig.add_axes([0.85, 0.15, 0.05, 0.7])
cbar4 = heatReflectFig.colorbar(c4, cax=cbar_ax4)
cbar4.set_label('Charge', rotation=270,size=20,labelpad=24)
cbar_ax4.tick_params(labelsize=16)

if singleEvent:
	heatFig.savefig("{}/{}_pxlHeatMap.png".format(savedir,runID))
	heatReflectFig.savefig("{}/{}_pxlSkyHeatMap.png".format(savedir,runID))
else:
	heatFig.savefig("{}/{}_avgpxlHeatMap.png".format(savedir,runID))
	heatReflectFig.savefig("{}/{}_avgpxlSkyHeatMap.png".format(savedir,runID))
	
"""
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
if movie:
	for samp in range(nSamples):
		sampleHeatArray = reduced_ampl[:,:,:,samp]
		sampleHeatArray = sampleHeatArray.reshape((len(modList),64))
		physSampHeatArr = np.zeros([nModules,8,8])
		physSampHeatArr[:,row,col] = sampleHeatArray
		
		for modInd in range(len(modList)):
			# determine the location of the module in the gridspace
			if full:
				reflectList = [4, 3, 2, 1, 0]
				loc = tuple(np.subtract(posGrid[modPos[modList[modInd]]],(1,1)))
				locReflect = tuple([loc[0],reflectList[loc[1]]])
			else:
				reflectList = [3, 2, 1, 0]
				loc = tuple(np.subtract(posGrid[modPos[modList[modInd]]],(2,1)))
				locReflect = tuple([loc[0],reflectList[loc[1]]])
			# modules in odd columns are rotated by 180 degrees
			# these are even columns here, because gridspec uses 0-based indexing
			if loc[1]%2==0:
				physSampHeatArr[modInd,:,:]=np.rot90(physSampHeatArr[modInd,:,:],k=2)
			
			SampReflectFig = plt.figure('Heat Map Sample {}'.format(samp), (18.,15.))
			ax_samp = plt.subplot(gs[locReflect])
			c_samp = ax_samp.pcolor(physSampHeatArr[modInd,:,::-1], vmin=0, vmax=1300)
			# take off axes
			ax_samp.axis('off')
			ax_samp.set_aspect('equal')
			
		SampReflectFig.subplots_adjust(right=0.8,top=0.9,bottom=0.1)
		cbar_samp_ax = SampReflectFig.add_axes([0.85, 0.15, 0.05, 0.7])
		cbar_samp = SampReflectFig.colorbar(c_samp, cax=cbar_samp_ax)
		cbar_samp.set_label('ADC Counts', rotation=270,size=20,labelpad=24)
		cbar_samp_ax.tick_params(labelsize=16)
		try:
			if singleEvent:
				os.mkdir('{}/movie/{}'.format(savedir,runID))
			else:
				os.mkdir('{}/movie/{}_avg'.format(savedir,runID))
		except:
			pass
		print "samp no", samp
		if singleEvent:
			SampReflectFig.savefig("{}/movie/{}/{}_pxlSkyHeatMap.png".format(savedir,runID,samp))
		else:
			SampReflectFig.savefig("{}/movie/{}_avg/{}__pxlSkyHeatMap.png".format(savedir,runID,samp))
		plt.close(SampReflectFig)

