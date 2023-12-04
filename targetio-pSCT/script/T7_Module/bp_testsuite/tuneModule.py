import numpy as np
import sys
import os
import target_driver
import time
import pymysql
import logging
import piCom

# have to give it the full filename if running as a standalone program

nasic = 4
nchannel = 16
ngroup = 4

# this should eventually be changed to an env variable
homedir = os.environ['HOME']
tunedDataDir = '%s/target5and7data/module_assembly' % homedir

# stores the identifying dataset associated with the tuned values of each module
moduleDict = {
	1:'1_20180326_1107',2:'2_20180416_1713',3:'3_20180417_0939',4:'4_20180322_1824',
	6:'6_20180417_1126',9:'9_20180417_1330',
	100:'100_20160108_1654',101:'101_20160108_1534',106:'106_20180329_1044', 107:'107_20160111_0600',
	108:'108_20160111_1006',110:'110_20160112_0626',111:'111_20160112_1023',
	112:'112_20160112_1150',113:'113_20160115_0537',114:'114_20160112_2057',
	115:'115_20180410_1051',
	116:'116_20160112_2218',118:'118_20160112_2351',119:'119_20160113_0109',
	121:'121_20180410_1701',123:'123_20160113_0417',124:'124_20160113_0541',
	125:'125_20160113_0703',126:'126_20180416_1113',128:'128_20160113_1009'}

moduleDict_25_degree = {
	1:'1_20180423_1653'
	2:'2_20180423_1705'
	3:'3_20180423_1718'
	4:'4_20180424_1106'
	6:'6_20180423_1731'
	9:'9_20180423_1744'
	118:'118_20180418_1242',
	125:'125_20180418_1255',
	126:'126_20180418_1307',
	101:'101_20180418_1345',
	119:'119_20180418_1400',
	108:'108_20180418_1411',
	121:'121_20180418_1423',
	110:'110_20180418_1436',
	115:'115_20180418_1228',
	123:'123_20180418_1448',
	124:'124_20180418_1502',
	112:'112_20180418_1203',
	100:'100_20180418_1513',
	111:'111_20180418_1525',
	114:'114_20180418_1537',
	107:'107_20180418_1549',
	}

# Former entry for 126: '126_20160113_0837'
# Former entry for 121: 121:'121_20160113_0230'
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

	logging.info( Vofs1 )
	logging.info( Vofs2 )
	logging.info( PMTref4 )

        return [Vofs1, Vofs2, PMTref4]

def writeBoard(module,Vped,Vofs1,Vofs2,PMTref4):
	# write Vped
	module.WriteSetting('Vped_value',Vped)
	time.sleep(0.1)
	
	# write Vofs1, Vofs2, PMTref4
	for asic in range(4):
		for group in range(4):
			for ch in range(group*4,group*4+4,1):
				time.sleep(0.1)
				module.WriteASICSetting("Vofs1_%s"%(ch),asic,int(Vofs1[asic][ch]),True) 
				time.sleep(0.1)
				module.WriteASICSetting("Vofs2_%s"%(ch),asic,int(Vofs2[asic][ch]),True)
			time.sleep(0.1)
			module.WriteASICSetting("PMTref4_%s"%(group),asic,int(PMTref4[asic][group]),True)



# needs module, 2 module dicts, and list of vtrim voltages (or alternatively, a list of vbias voltages)
def getTrims(moduleID):
	#Vbiaslist = []

	nQuads = 100
	hiSide = 70.00 #V
	
	logging.info( moduleID ) #YYY module ID

	# connect to MySQL
	try:
		sql = pymysql.connect(port=3406, host='romulus.ucsc.edu', user='CTAreadonly', password='readCTAdb',database='CTAoffline')
	except:
		sql = pymysql.connect(port=3406, host='remus.ucsc.edu', user='CTAreadonly', password='readCTAdb',database='CTAoffline')
	cursor = sql.cursor()

	# figure out the FPM from SQL
	select_position = "SELECT sector, position FROM associations WHERE module=%(module)s"
	cursor.execute(select_position,{'module':moduleID})
	FPM = cursor.fetchone()
	logging.info( FPM )

	# get quadrant associations for FPM
	select_quads = "SELECT q0, q1, q2, q3 FROM associations WHERE module=%(module)s"
	cursor.execute(select_quads,{'module':moduleID})
	quads = cursor.fetchone()
	logging.info( quads[::-1] )

	# grabs the 4 trim voltages of each ASIC/quadrant
	select_trims = "SELECT g0, g1, g2, g3 FROM trimlist WHERE quad=%(quad)s"

	trimsToWrite = []
	
	# creates a list of the trim voltages for each pixel in each ASIC/quadrant (16 in total)
	for quad in quads:
		cursor.execute(select_trims,{'quad':quad})
		trims = cursor.fetchone()
		quadtrims = []
		for trim in trims:
			quadtrims.append(trim)#FIXME
		quadtrims = quadtrims[::-1]
		if moduleID==124 and quad==17:
			quadtrims = quadtrims[::-1] #FIXME
		if moduleID==119 and quad==49: #FIXME
			temp0=quadtrims[0]
			temp1=quadtrims[1]
			temp2=quadtrims[2]
			temp3=quadtrims[3]
			quadtrims[0]=temp3
			quadtrims[1]=temp1
			quadtrims[2]=temp2
			quadtrims[3]=temp0
		trimsToWrite.append(quadtrims)
	
	# ASICs have a reverse correspondence with quadrants
	# a0=q3, a1=q2, a2=q1, a3=q0
	# we reverse the list here because
	# we use the ASICs as indices to set trim voltages in setTrims
	trimsToWrite = trimsToWrite[::-1]
	
	cursor.close()
	sql.close()

	return trimsToWrite




def setTrims(module, trimsToWrite, HV, addBias=0):
	"""
	Information on what's done here can be found at: https://datasheets.maximintegrated.com/en/ds/MAX5713-MAX5715.pdf
	"""
	nAsic = 4
	nTrgPxl = 4
	asicDict = {0 : 0b0001, 1 : 0b0010, 2 : 0b0100, 3 : 0b1000}
	if(HV==1):
		print "HV is being switched ON"
		module.WriteSetting("HV_Enable", 0b1)#FIXME
		module.WriteSetting("SelectLowSideVoltage",0b1)#FIXME
		# selects all asics
		module.WriteSetting("HVDACControl",0b1111)#FIXME
		# sets reference voltage for all asics to 4.096 V 
		module.WriteSetting("LowSideVoltage",0x73000)
		for asic in range(nAsic):
			module.WriteSetting("HVDACControl",asicDict[asic])
			for tpxl in range(nTrgPxl):
				# picks correct trim voltage from list, converts to mV, and converts that to hex
				# db includes -0.6 V trim subtraction from GT breakdown values
				intTrim = int( (trimsToWrite[(asic)][tpxl])*1000+addBias)  #FIXME get rid of 600
				codeload = 0x30000
				triggerPixel = int("0x%s000"%(tpxl),16)
				hexWrite = (intTrim | codeload | triggerPixel)
				# value written here will be 0x3XYYY
				# 3 specifies that this is a code n load n operation
				# X specifies trigger ch/pxl as either 0,1,2,3 (in hex)
				# YYY specifies the low side voltage in mV
				logging.info( intTrim )
				logging.info( module.WriteSetting("LowSideVoltage",hexWrite) )
	else:
		print "HV stays OFF"
		module.WriteSetting("HV_Enable", 0b0)#FIXME
		module.WriteSetting("SelectLowSideVoltage",0b0)#FIXME
		# selects all asics
		module.WriteSetting("HVDACControl",0b0000)#FIXME

def setTrimsW(module, moduleID, trimsToWrite):
	
	# connect to MySQL
	sql = pymysql.connect(port=3406, host='romulus.ucsc.edu', user='CTAreadonly', password='readCTAdb',database='CTAoffline')
	cursor = sql.cursor()

	# figure out the FPM from SQL 
	select_position = "SELECT sector, position FROM associations WHERE module=%(module)s"
	cursor.execute(select_position,{'module':moduleID})
	FPM = cursor.fetchone()
	pos = FPM[1]

	cursor.close()
	sql.close()
	
	closeList = 	[[[1,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]],
			[[0,0,0,0],[0,0,0,0],[1,1,1,1],[1,0,1,1]],
			[[1,1,1,1],[1,1,1,0],[0,0,0,0],[0,0,0,0]],
			[[0,0,0,0],[0,0,0,0],[0,0,1,0],[0,0,0,0]],
			[[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]],
			[[1,1,1,1],[0,0,0,0],[1,1,1,1],[0,0,0,0]],
			[[1,0,1,0],[1,1,0,1],[0,0,0,0],[0,1,0,0]],
			[[0,0,0,0],[0,0,0,1],[1,0,1,0],[0,1,1,1]],
			[[1,1,1,1],[0,0,0,0],[1,1,1,1],[0,0,0,0]],
			[[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]],
			[[1,1,1,1],[1,0,0,0],[1,1,1,1],[0,0,0,0]],
			[[0,0,0,0],[0,0,0,0],[0,0,1,0],[0,0,0,0]],
			[[1,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]],
			[[1,1,1,1],[0,0,0,0],[1,1,1,1],[0,0,1,0]],
			[[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]],
			[[0,0,0,0],[0,0,0,0],[1,1,1,1],[1,0,1,0]],
			[[1,0,1,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]],
			[[0,0,0,0],[0,0,0,0],[1,0,1,0],[0,0,0,0]],
			[[1,1,1,1],[1,0,1,0],[0,0,0,0],[0,0,0,0]]]
	nAsic = 4
	nTrgPxl = 4
	asicDict = {0 : 0b0001, 1 : 0b0010, 2 : 0b0100, 3 : 0b1000}
	module.WriteSetting("HV_Enable", 0b1)#FIXME
	module.WriteSetting("SelectLowSideVoltage",0b1)#FIXME
	# selects all asics
	module.WriteSetting("HVDACControl",0b1111)#FIXME
	# sets reference voltage for all asics to 4.096 V 
	module.WriteSetting("LowSideVoltage",0x73000)
	for asic in range(nAsic):
		module.WriteSetting("HVDACControl",asicDict[asic])
		for tpxl in range(nTrgPxl):
			# picks correct trim voltage from list, converts to mV, and converts that to hex
			# db includes -0.6 V trim subtraction from GT values
			if not closeList[pos][asic][tpxl]:
				intTrim = int(4.095*1000)
			else:
				intTrim = int((trimsToWrite[(asic)][tpxl])*1000)
			codeload = 0x30000
			triggerPixel = int("0x%s000"%(tpxl),16)
			hexWrite = (intTrim | codeload | triggerPixel)
			# value written here will be 0x3XYYY
			# 3 specifies that this is a code n load n operation
			# X specifies trigger ch/pxl as either 0,1,2,3 (in hex)
			# YYY specifies the low side voltage in mV
			logging.info( intTrim )
			logging.info( module.WriteSetting("LowSideVoltage",hexWrite) )


def raiseTriggerThreshold(module):

	time.sleep(1)
	print "Set trigger levels:"
	for asic in range(4):
		for group in range(4):
				print group, asic, 0x0
				module.WriteASICSetting("Thresh_{}".format(group), asic, 0x0, True) #sets the trigger threshold that has been determined in another test
				time.sleep(0.1)

####Trial code for setting trig thresh for certain PE value for each trigger group
Default_ThreshLevelList = [729, 754, 804, 679, 665, 743, 754, 615, 604, 643, 654, 540, 565, 704, 679, 554] #these trigger levels are for 20PE setting
def setTriggerLevel(module, ThreshLevelList=Default_ThreshLevelList):
	time.sleep(1)
	#print "Set trigger levels:"
	for asic in range(4):
		for group in range(4):
			#print group, asic, ThreshLevelList[(asic*4)+group]
			module.WriteASICSetting("Thresh_{}".format(group), asic, ThreshLevelList[(asic*4)+group], True)
			#time.sleep(0.1)


def setTriggerWidth(module, wbias):

	time.sleep(1)
	for asic in range(4):
		for group in range(4):
			module.WriteASICSetting("Wbias_{}".format(group), asic, int(wbias), True) #sets the trigger width
			time.sleep(0.1)


def getTunedWrite(moduleID,module,Vped, pi, HV=1, numBlock=2, addBias=0, wbias=985):
	# use dict to find dataset to read in from moduleID
	if(moduleID in moduleDict_25_degree.keys() ):
		dataset = moduleDict_25_degree[moduleID]
	else:
		dataset = moduleDict[moduleID]

	# create filename from it
	print tunedDataDir
	print dataset
	filename = "%s/%s/report.txt" % (tunedDataDir,dataset)
	print filename
	# read tuning values in from file
	#piCom.setTriggerMask(pi) #We get data if here
	allVals = readVals(filename)
	Vofs1 = allVals[0]
	Vofs2 = allVals[1]
	PMTref4 = allVals[2]
	# write them
	writeBoard(module,Vped,Vofs1,Vofs2,PMTref4)
	time.sleep(1.0)

	trimsToWrite = getTrims(moduleID)
	logging.info(trimsToWrite)
	logging.info(Vped)
	logging.info(Vofs1)
	logging.info(Vofs2)
	logging.info(PMTref4)

	time.sleep(0.5)
	setTrims(module, trimsToWrite, HV, addBias)

	#setTrimsW(module, moduleID, trimsToWrite) #FIXME
	time.sleep(0.5)

	raiseTriggerThreshold(module) #Rais threshold to max, to prevent triggering
	time.sleep(0.5)
	##setTriggerWidth(module, wbias)	
	time.sleep(0.5)
	print "Setting number of blocks to", numBlock
	module.WriteSetting("NumberOfBlocks", numBlock-1)


	#return list of pmtref4 vals
	return PMTref4

if __name__ == "__main__":
	filename=sys.argv[1]
	readVals(filename)

