import target_driver
import os
import time,datetime
import target_io
import run_control
#import BrickPowerSupply
import numpy
#import argparse
import random
import tuneModule
import sqlSetTrimTest
from LED import *
import logging
import tuneModule
import analyzeTriggerThreshScan
import getSerial
import powerCycle
import runInit



def efficiency(tester, timeint, elapsed, inputf):
        tester.StartTriggerEfficiencyCounter(timeint)
        while not tester.IsTriggerEfficiencyCounterOutsideDeadTimeCompleted():
                time.sleep(0.05)
        count = tester.GetTriggerEfficiencyCounterOutsideDeadTime()
        eff = count/(inputf*elapsed)
        return eff

def trigCount(tester, timeint, elapsed):
        tester.StartTriggerEfficiencyCounter(timeint)
        while not tester.IsTriggerEfficiencyCounterOutsideDeadTimeCompleted():
                time.sleep(0.05)
        time.sleep(0.2)
        #print "get Efficiency now!"
        count = tester.GetTriggerEfficiencyCounterOutsideDeadTime()
        rate = float(count) / elapsed
        return rate

"""
module,tester: objects for the module and tester board
numBlock: number of blocks for datataking
HV: boolean, deciding whether to activate the HV for these tests
"""
def trigThreshScan(module, tester, moduleID, testASIC, testGroup, dataset, testDir, numBlock=2, HV=1, Vped=1106, deadtime=500, inputf=100,enableReadout=1):
        
        outRunList=[]
        outFileList=[]
        
        # 0 if looking at trigger rate, 1 if looking at trigger efficiency
        doEff = 0

        # set to 1 if looking at trigger efficiencies
        threshvals = numpy.arange(50,2600,25)
        #threshvals = threshvals[::-1]
        elapsed = 1.0 # run duration in seconds
        duration = elapsed / 8.e-9 # elapsed s / 8 ns => duration time of counting in 8 ns 
        timeint = int(duration)
        
        ld = LED()
        ld.setLED(freq=inputf, trig_output=1, flasher_output=1)

        hostname = run_control.getHostName()
        outdirname = run_control.getDataDirname(hostname)
        #runID = run_control.incrementRunNumber(outdirname)

        #Set Vped, enable all channels for readout
        module.WriteSetting("Vped_value", Vped)
        module.WriteSetting("EnableChannelsASIC0", 0xffff)
        module.WriteSetting("EnableChannelsASIC1", 0xffff)
        module.WriteSetting("EnableChannelsASIC2", 0xffff)
        module.WriteSetting("EnableChannelsASIC3", 0xffff)
        module.WriteSetting("Zero_Enable", 0x1)

        module.WriteSetting("NumberOfBlocks", numBlock-1)
        module.WriteSetting("TriggerDelay", 8)
        if(HV):
                fail = module.WriteSetting("HV_Enable", 0x1)
                logging.info("HV ON: %d", fail)
        else:
                fail = module.WriteSetting("HV_Enable", 0x0)
                logging.info("HV OFF: %d", fail)
        time.sleep(0.1)

        # internal trigger
        effout1 = testDir + '/triggerEfficiency_{}/'.format(dataset)
        effout2 = testDir + '/triggerEfficiency_{}/{}/'.format(dataset, deadtime)
        effout = testDir + '/triggerEfficiency_{}/{}/{}/'.format(dataset, deadtime,enableReadout)
        try:
                os.mkdir(effout1)
                os.chmod(effout, 0o777)
        except:
                logging.warning("directory %s already exists", effout1)

        try:
                os.mkdir(effout2)
                os.chmod(effout2, 0o777)
        except:
                logging.warning("directory %s already exists", effout2)
        try:
                os.mkdir(effout)
                os.chmod(effout, 0o777)
        except:
                logging.warning("directory %s already exists", effout)

        # list built to check for errors in rates
        trigThreshRate = []        
        
        triggerDly=580
        tester.SetTriggerModeAndType(0b00, 0b00)                

        tester.SetTriggerDeadTime(deadtime)
        module.WriteSetting("TriggerDelay",triggerDly)
        # disabling everything first
        for asic in range(4):
                for group in range(4):
                        tester.EnableTriggerCounterContribution(asic, group, False)
                        tester.EnableTrigger(asic,group,False)
        # loop to count triggers
        asic = testASIC
        group = testGroup
        outname = 'a{}g{}.txt'.format(asic,group)
        effoutname = effout+outname
        logging.info("saving in %s", effoutname)
        outFile = open(effoutname, 'w')
        outFileList.append(effoutname)
        tester.EnableTriggerCounterContribution(asic,group,True)
        if enableReadout:
                tester.EnableTrigger(asic,group,True)
        Thresh_group = "Thresh_{}".format(group)
        for thresh in threshvals:
                module.WriteASICSetting(Thresh_group.format(group), asic, int(thresh), True)
                time.sleep(0.2)
                if doEff:
                        eff = efficiency(tester, timeint, elapsed, inputf)
                else:
                        eff = trigCount(tester, timeint, elapsed)
                trigThreshRate.append(eff)                
                logging.info("%d   %d   %d   %f", asic, group, int(thresh), eff)
                outFile.write("%d %f\n"%(thresh, eff))
        outFile.close()
        if enableReadout:
                tester.EnableTrigger(asic,group,False)
        tester.EnableTriggerCounterContribution(asic, group, False)

        ld.LEDoff()

        if HV:
                module.WriteSetting("HV_Enable", 0x0)

        # initially considered done, unless the rates are all 0
        groupDone = 1
        # to count the # of 0's in the rates 
        zeroCount = 0
        for rate in trigThreshRate:
                if rate == 0:
                        zeroCount += 1
        # if it's filled with 0's mark it for rerun
        if zeroCount == len(trigThreshRate):
                groupDone = 0
                return outRunList, outFileList, groupDone        

        return outRunList, outFileList, groupDone


#module.CloseSockets()
#tester.CloseSockets()

if __name__ == "__main__":

        moduleID,FPM = getSerial.getSerial()
        FPM = "{}.{}".format(FPM[0],FPM[1])
        moduleID = int(moduleID)

        hostname = run_control.getHostName()
        outdirname = run_control.getDataDirname(hostname)
        testDir = outdirname + 'test_suite_output/FEE'+str(moduleID)+'FPM'+FPM

        #get the dataset 
        timestamp = time.time()
        dataset = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M')

        #Begin power cycle
        bps = powerCycle.powerCycle()

        #Begin initialization
        module, tester = runInit.Init()
        Vped = 1106

        #Begin tuning
        tuneModule.getTunedWrite(moduleID,module,Vped)
        freq = 100
        enableReadouts = [0,1]
        for item in enableReadouts:
                #Run a threshold scan
                for asic in range(4):
                        for group in range(4):
                                trigThreshDone = False
                                trigThreshCounter = 0
                                #trigThreshDone checks to make sure we don't see a scan with 0 triggers everywhere
                                while not trigThreshDone and trigThreshCounter < 2:
                                        outRunList, outFileList,trigThreshDone = trigThreshScan(module, tester, moduleID, asic, group, dataset, testDir, deadtime=12500, inputf=freq, enableReadout=item)
                                        runInit.Close(module,tester)
                                        bps = powerCycle.powerCycle()
                                        module, tester = runInit.Init()
                                        tuneModule.getTunedWrite(moduleID,module,Vped)
                                        trigThreshCounter += 1

        #analysis
        analyzeTriggerThreshScan.analyzeThreshScan(dataset, testDir, deadTimeList, freq)











