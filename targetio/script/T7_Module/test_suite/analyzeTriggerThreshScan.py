import numpy as np
import matplotlib.pyplot as plt
import os.path
import run_control
import logging


def checkData(data, freq):
    slopeDiff=[]
    temp1 = 0
    temp2 = 0
    for i in range(data.shape[0]-2):
        xdata = data[i:i+2,0]
        ydata = data[i:i+2,1]
        if(xdata[0]<1700):
                slope = getSlope(xdata,ydata)
                if(i>2):
                        slopeDiff.append(slope - temp1 + temp2)
                        temp2 = temp1
                        temp1 = slope

    slopeDiff = np.array(slopeDiff)
    return slopeDiff
    
    
def getSlope(xdata, ydata):
    slope=[]
    for i in range(xdata.shape[0]-1):
        if(ydata[i]>0): slope.append( (ydata[i+1] - ydata[i])/(xdata[i+1] - xdata[i])/ydata[i] )
        else: slope.append( (ydata[i+1] - ydata[i])/(xdata[i+1] - xdata[i]) )
    slope = np.array(slope)
    return slope.mean()




def analyzeThreshScan(dataset, testDir, deadTimeList, freq):
        hostname = run_control.getHostName()
        outdirname = run_control.getDataDirname(hostname)
        label = "dt = 4us"
        fig, ax = plt.subplots(nrows=4, ncols=4, figsize=(34,24))
        fig1, ax1 = plt.subplots(nrows=4, ncols=4, figsize=(34,24))

        

        for deadTime in deadTimeList:
           for enable in range(0,2):
                dirname = testDir + "/triggerEfficiency_" + dataset + "/" + str(deadTime) + "/" + str(enable)
                if(os.path.exists(dirname ) ):
                        data=[]
                        slopesDiff=[]
                        actTime = round(deadTime/125.0,1)
                        label = "dt = {}us".format(actTime)
                        if(enable):
                                label = label+", trig. en."

                        logging.debug("The directory name is: %s", dirname)
                        for asic in range(4):
                                for group in range(4):
                                        filename=dirname+"/a{}g{}".format(asic,group)+".txt"
                                        if(os.path.isfile(filename) ):
                                                logging.debug("Reading values: %d  %d  %s", asic, group, filename)
                                                newData = np.loadtxt(filename)
                                                data.append(newData)
                                                slopesDiff.append( checkData(newData, freq) )
                                        
                        logging.debug("Length of data is: %d", len(data))
                        for ch in range(0,16):
                                dat=ch
                                thresh = data[dat][:,0]
                                rate = data[dat][:,1]
                                rate[rate<.01] = .01
                                ax[ch/4,ch%4].plot(thresh,rate, marker='o', label=label)
                                ax[ch/4,ch%4].tick_params(axis='x', labelsize=20)
                                ax[ch/4,ch%4].tick_params(axis='y', labelsize=20)
                                ax[ch/4,ch%4].set_yscale('log')
                                ax[ch/4,ch%4].set_ylim(bottom=10e-3,top=10e5)

                                ax1[ch/4,ch%4].plot(data[dat][:slopesDiff[dat].shape[0],0],slopesDiff[dat][:], marker='o', label=label)
                                ax1[ch/4,ch%4].tick_params(axis='x', labelsize=20)
                                ax1[ch/4,ch%4].tick_params(axis='y', labelsize=20)
        #                        ax1[ch/4,ch%4].set_yscale('log')
                                if(abs(slopesDiff[dat]).max()>0.6):
                                        logging.warning("Found bad slope %f in group %d on asic %d with dead time %f us. Readjust deadTime!",abs(slopesDiff[dat]).max(), ch%4, ch/4, actTime)
        
        for ch in range(16):
                ax[ch/4,ch%4].legend(loc=0, fontsize=18)
                ax[ch/4,ch%4].set_xlim(-200,2700)        
                ax1[ch/4,ch%4].legend(loc=0, fontsize=18)
                ax1[ch/4,ch%4].set_xlim(-200,2700)        
        figName = testDir+"/threshScan_"+dataset+".png"
        fig.savefig(figName)
        fig1Name = testDir+"/threshScanSlopeDiff_"+dataset+".png"
        fig1.savefig(fig1Name)


        if(os.path.isfile(figName) ):
                logging.info("Threshcan analysis finished successffully.")
                return 0
        else:
                logging.error("ThreshScan Figure could not be produced.")
                return 1

if __name__ == "__main__":
        dataset = '20160831_1431'
        #testDir = '/Users/colinadams/target5and7data/test_suite_output/FEE112FPM4.8'
        testDir = '/Users/colinadams/outputIndividual'
        deadTimeList = [12500]
        freq = 100
        analyzeThreshScan(dataset, testDir, deadTimeList, freq)

