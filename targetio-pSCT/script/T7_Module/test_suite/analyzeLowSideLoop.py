import numpy as np
import os
import run_control
import matplotlib.pyplot as plt

def getSlope(data):
	slope=[]
	for i in range(data.shape[0]-1):
		slope.append(data[i+1] - data[i] )
	slope = np.array(slope)
	return slope


def analyzeLowSideLoop(outputDir, data_set, runList):

	outFile = outputDir +"/lowSideCheckValues"+data_set+".log"

	hostname = run_control.getHostName()
	outdirname = outputDir
	#runList=[296598, 296700]
	highSide = 70
	lowSideCounts = np.arange(0,4081,40)
	print lowSideCounts.shape
	lowSideVoltage = lowSideCounts*4.096/4095
	rumChannels = 64
	
	meanCurrentList=[]
	sumCurrentList=[]
	counter=0
	allCurrents=[]
	diffCurrents=[]
	maxCurrentSlope=np.zeros(64)
	minCurrentSlope=np.zeros(64)
	maxCurrent=np.zeros(64)
	minCurrent=np.zeros(64)
	maxCurrentDiff=np.zeros(64)
	for runID in range(runList[0], runList[1]+1):
		inFile = outdirname+"/lowSide_run"+str(runID)+".log"
		currents = np.loadtxt(inFile)
		allCurrents.append(currents)
		meanCurrentList.append(currents[0:64].mean())
		sumCurrentList.append(currents[0:64].sum())
		diffCurrents.append( currents[0:64] - currents[0:64].mean() )
		#print "found current of", meanCurrentList[counter], "uA for Lowsidevoltage of", lowSideVoltage[counter],"V."
		counter+=1

	allCurrents = np.array(allCurrents)
	diffCurrents = np.array(diffCurrents)

	f = open(outFile,'w')
	f.write("Channel   Max-Current-slope Min-current_slope   Max-Current-diff    Max-current    Min-current\n")
	for i in range(64):
		maxCurrentSlope[i] =  (getSlope(allCurrents[:,i])).max()
		minCurrentSlope[i] =  (getSlope(allCurrents[:,i])).min()
		maxCurrentDiff[i] = abs(diffCurrents[:,i]).max()
		maxCurrent[i] = allCurrents[:,i].max()
		minCurrent[i] = allCurrents[:,i].min()
		f.write("%d   %f   %f   %f   %f   %f\n" % (i, maxCurrentSlope[i], minCurrentSlope[i], maxCurrentDiff[i], maxCurrent[i], minCurrent[i]) )

	sumCurrentList = np.array(sumCurrentList)

	#produce plots
	fig1 = plt.figure(figsize=(8,8))
	plt.xlabel("Low side voltage in V")
	plt.ylabel("Single channel current in uA")
	#print lowSideVoltage.shape, allCurrents.shape
	for i in range(0,64):
		plt.plot(lowSideVoltage,allCurrents[:,i])
	
	filename = outputDir+"/SingleChCurrent"+str(data_set)+".png"	
	fig1.savefig(filename)
	
	
	fig2 = plt.figure(figsize=(8,8))
	plt.xlabel("Low side voltage in V")
	plt.ylabel("Global current draw in mA and sum of indiv.")
	#print lowSideVoltage.shape, allCurrents.shape
	plt.plot(lowSideVoltage,allCurrents[:,64]/2.0, label = 'global current')
	plt.plot(lowSideVoltage,sumCurrentList/1e3, label = 'sum of indiv. currents')
	plt.legend(loc=0)
	
	filename = outputDir+"/GlobalCurrent"+str(data_set)+".png"	
	fig2.savefig(filename)



	fig3 = plt.figure(figsize=(8,8))
	plt.xlabel("Low side voltage in V")
	plt.ylabel("Global voltage in V")
	#print lowSideVoltage.shape, allCurrents.shape
	plt.plot(lowSideVoltage,allCurrents[:,65]*20.854/1e3)
	
	filename = outputDir+"/GlobalVoltage"+str(data_set)+".png"	
	fig3.savefig(filename)
	
	
	
	fig4 = plt.figure(figsize=(8,8))
	plt.xlabel("Low side voltage in V")
	plt.ylabel("Mean single chanel current in uA")
	#print lowSideVoltage.shape, allCurrents.shape
	plt.plot(lowSideVoltage,meanCurrentList)
	filename = outputDir+"/MeanChCurrent"+str(data_set)+".png"	
	fig4.savefig(filename)


if __name__ == "__main__":
	analyzeLowSideLoop("/Users/colinadams/test_folder/","ok",[1])
