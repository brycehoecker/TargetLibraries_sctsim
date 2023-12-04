import numpy as np
import sys
import os
import target_driver

# have to give it the full filename if running as a standalone program

nasic = 4
nchannel = 16
ngroup = 4

# this should eventually be changed to an env variable
homedir = os.environ['HOME']
tunedDataDir = '%s/target5and7data/module_assembly' % homedir

# stores the identifying dataset associated with the tuned values of each module
moduleDict = {
	100:'100_20160108_1654',101:'101_20160108_1534',107:'107_20160111_0600',
	108:'108_20160111_1006',110:'110_20160112_0626',111:'111_20160112_1023',
	112:'112_20160112_1150',113:'113_20160115_0537',114:'114_20160112_2057',
	116:'116_20160112_2218',118:'118_20160112_2351',119:'119_20160113_0109',
	121:'121_20160113_0230',123:'123_20160113_0417',124:'124_20160113_0541',
	125:'125_20160113_0703',126:'126_20160113_0837',128:'126_20160113_1009'}

# takes report from test suite run, scans it for tuning values, returns them in an array
def readVals(filename):
        f = open(filename)

        Vofs1 = np.zeros((nasic, nchannel),dtype='int')
        Vofs2 = np.zeros((nasic, nchannel),dtype='int')
        PMTref4 = np.zeros((nasic, ngroup),dtype='int')
        for l in f.readlines():
            if "Vofs1" in l[:5]:
                asic = int(l[31:].split("ASIC ")[1].split("Channel")[0])
                channel = int(l[31:].split("Channel")[1].split(":")[0])
                Vofs1[asic][channel] = int(l[31:].split(": ")[1].split("DAC")[0])
            if "Vofs2" in l[:5]:
                asic = int(l[31:].split("ASIC ")[1].split("Channel")[0])
                channel = int(l[31:].split("Channel")[1].split(":")[0])
                Vofs2[asic][channel] = int(l[31:].split(": ")[1].split("DAC")[0])
            if "PMTref4" in l[:7]:
                asic = int(l[31:].split("ASIC ")[1].split("Group")[0])
                group = int(l[31:].split("Group")[1].split(":")[0])
                PMTref4[asic][group] = int(l[31:].split(": ")[1].split("DAC")[0])

        Vofs1NP = Vofs1
        Vofs2NP = Vofs2
        PMTref4NP = PMTref4

        Vofs1 = Vofs1.tolist()
        Vofs2 = Vofs2.tolist()
        PMTref4 = PMTref4.tolist()

	print Vofs1
	print Vofs2
	print PMTref4

        return [Vofs1, Vofs2, PMTref4]

def writeBoard(module,Vped,Vofs1,Vofs2,PMTref4):
	# write Vped
	module.WriteSetting('Vped_value',Vped)
	
	# write Vofs1, Vofs2, PMTref4
	for asic in range(4):
		for group in range(4):
			for ch in range(group*4,group*4+4,1):
				module.WriteASICSetting('Vofs1_{}'.format(ch),asic,int(Vofs1[asic][ch]),True) 
				module.WriteASICSetting('Vofs2_{}'.format(ch),asic,int(Vofs2[asic][ch]),True)
			module.WriteASICSetting('PMTref4_{}'.format(group),asic,int(PMTref4[asic][group]),True)

def getTunedWrite(moduleID,module,Vped):
	# use dict to find dataset to read in from moduleID
	dataset = moduleDict[moduleID]
	# create filename from it
	filename = '{}/{}/report.txt'.format(tunedDataDir,dataset)
	# read tuning values in from file
	allVals = readVals(filename)
	Vofs1 = allVals[0]
	Vofs2 = allVals[1]
	PMTref4 = allVals[2]
	# write them
	writeBoard(module,Vped,Vofs1,Vofs2,PMTref4)

	#return list of pmtref4 vals
	return PMTref4

if __name__ == "__main__":
	filename=sys.argv[1]
	readVals(filename)

