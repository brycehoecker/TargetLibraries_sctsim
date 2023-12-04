import target_driver
import target_io
import target_calib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec
import datetime
import time
import sys
import os
import pickle

argList = sys.argv
runID = int(argList[1])
start_event = int(argList[2])

end_event = start_event
step = 1

if len(argList) > 3:
    end_event = int(argList[3])
    if len(argList) > 4:
        step = int(argList[4])

eventList = [i for i in range(start_event, end_event+1, step)]

savedir = f"/data/software/CCC/TargetCalib/trunk/test/run{runID}/"

try:
    os.mkdir(savedir)
except:
    pass

nasic = 4
nch = 16

chPerPacket = 32

datadir = "/data/software/CCC/TargetCalib/trunk/test/"
filename = f"{datadir}run{runID}_calibrated.r1"

print(f"Reading file: {filename}")

modList = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100, 103, 106, 107, 108, 111, 112, 114, 115, 119, 121, 123, 124, 125, 126]
nModules = len(modList)

modPos = {      4:5, 5:6, 1:7, 3:8, 2:9,
                103:11, 125:12, 126:13, 106:14, 9:15,
                119:17, 108:18, 110:19, 121:20, 8:21,
                115:23, 123:24, 124:25, 112:26, 7:27,
                100:28, 111:29, 114:30, 107:31, 6:32,
                101:14} #101 was formerly in slot 14 before it broke

posGrid =       {5:(1,1), 6:(1,2), 7:(1,3), 8:(1,4), 9:(1,5),
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

calreader = target_io.WaveformArrayReader(filename)
n_pixels = calreader.fNPixels
n_samples = calreader.fNSamples
n_events = calreader.fNEvents

waveforms = np.zeros((n_pixels, n_samples), dtype=np.float32)

physHeatArr = np.zeros[nModules, 8, 8]

for event_index in eventList:
    calreader.GetR1Event(event_index, waveforms)
    peak = np.amax(waveforms[:, 20:], axis=1)
    peak = np.reshape(peak, (nModules, -1))
    for mod in range(len(peak)):
        if mod in range(9):
            peak[mod,:] /= 2.0

    physHeatArr[:, row, col] = peak

    maxZ = np.amax(peak)

    def calcLoc(modInd):
        reflectList = [4, 3, 2, 1, 0]
        loc = tuple(np.subtract(posGrid[modPos[modList[modInd]]], (1,1)))
        locReflect = tuple([loc[0], reflectList[loc[1]]])
        return loc, locReflect

    heatReflectFig = plt.figure('Heat Map Skyview', (18, 15))

    gs = gridspec.GridSpec(5,5)
    gs.update(wspace=0.04, hspace=0.04)

    for modInd in range(nModules):
        loc, locReflect = calcLoc(modInd)

        # modules in odd columns are rotated by 180 degrees
        # these are even columns here, because gridspec uses 0-based indexing
        if loc[1]%2==0:
            physHeatArr[modInd,:,:]=np.rot90(physHeatArr[modInd,:,:],k=2)

        # deal with skyview heat map
        plt.figure('Heat Map Skyview')
        ax4= plt.subplot(gs[locReflect])
        c4 = ax4.pcolor(physHeatArr[modInd,:,::-1], vmin=0, vmax=maxZ)
        # take off axes
        ax4.axis('off')
        ax4.set_aspect('equal')

    heatReflectFig.subplots_adjust(right=0.8,top=0.9,bottom=0.1)
    cbar_ax4 = heatReflectFig.add_axes([0.85, 0.15, 0.05, 0.7])
    cbar4 = heatReflectFig.colorbar(c4, cax=cbar_ax4)
    cbar4.set_label('Max ADC - baseline (ADC counts)', rotation=270,size=20,labelpad=24)
    cbar_ax4.tick_params(labelsize=16)
    heatReflectFig.savefig("{}/{}_ev{}_diff_pxlSkyHeatMap.png".format(savedir,runID, choose_event))

print("Event images saved to: ", savedir)
print("")

