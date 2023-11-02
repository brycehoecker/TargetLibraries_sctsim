import numpy as np
import sys
import os
import target_driver
import time
import pymysql
import logging


# have to give it the full filename if running as a standalone program

nasic = 4
nchannel = 16
ngroup = 4

# this should eventually be changed to an env variable
homedir = os.environ['HOME']
tunedDataDir = '%s/target5and7data/module_assembly' % homedir

# stores the identifying dataset associated with the tuned values of each module
moduleDict = {
    100:'100_20160108_1654',101:'101_20160108_1534',106:'106_20180329_1044',107:'107_20160111_0600',
    108:'108_20160111_1006',110:'110_20160112_0626',111:'111_20160112_1023',
    112:'112_20160112_1150',113:'113_20160115_0537',114:'114_20160112_2057',
    115:'115_20161003_1147',
    116:'116_20160112_2218',118:'118_20160112_2351',119:'119_20160113_0109',
    121:'121_20160113_0230',123:'123_20160113_0417',124:'124_20160113_0541',
    125:'125_20160113_0703',126:'126_20160113_0837',128:'128_20160113_1009'}

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

        # write Vofs1, Vofs2, PMTref4
        for asic in range(4):
                for group in range(4):
                        for ch in range(group*4,group*4+4,1):
                                module.WriteASICSetting('Vofs1_{}'.format(ch),asic,int(Vofs1[asic][ch]),True) 
                                module.WriteASICSetting('Vofs2_{}'.format(ch),asic,int(Vofs2[asic][ch]),True)
                        module.WriteASICSetting('PMTref4_{}'.format(group),asic,int(PMTref4[asic][group]),True)



# needs module, 2 module dicts, and list of vtrim voltages (or alternatively, a list of vbias voltages)
def getTrims(moduleID,FPM):
        #Vbiaslist = []

        nQuads = 100
        hiSide = 70.00 #V

        logging.info( moduleID ) #YYY module ID
        logging.info( FPM )

        # connect to MySQL
        sql = pymysql.connect(host='romulus.ucsc.edu', user='CTAreadonly', password='readCTAdb',database='CTAoffline', port=3406)
        cursor = sql.cursor()

        """
        # figure out the FPM from SQL 
        select_position = "SELECT sector, position FROM associations WHERE module=%(module)s"
        cursor.execute(select_position,{'module':moduleID})
        FPM = cursor.fetchone()
        logging.info( FPM )
        """

        # get quadrant associations for FPM
        select_quads = "SELECT q0, q1, q2, q3 FROM associations WHERE position = %(position)s AND sector=%(sector)s"
        cursor.execute(select_quads,{'sector':FPM[0],'position':FPM[1]})
        quads = cursor.fetchone()
        logging.info( quads )

        # grabs the 4 trim voltages of each ASIC/quadrant
        select_trims = "SELECT g0, g1, g2, g3 FROM trimlist WHERE quad=%(quad)s"

        trimsToWrite = []

        # creates a list of the trim voltages for each pixel in each ASIC/quadrant (16 in total)
        for quad in quads:
                cursor.execute(select_trims,{'quad':quad})
                trims = cursor.fetchone()
                quadtrims = []
                for trim in trims:
                        quadtrims.append(trim)
                quadtrims = quadtrims[::-1]
                trimsToWrite.append(quadtrims)

        # ASICs have a reverse correspondence with quadrants
        # a0=q3, a1=q2, a2=q1, a3=q0
        # we reverse the list here because
        # we use the ASICs as indices to set trim voltages in setTrims
        trimsToWrite = trimsToWrite[::-1]

        cursor.close()
        sql.close()

        return trimsToWrite

def setTrims(module, trimsToWrite):
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
                        intTrim = int((trimsToWrite[asic][tpxl])*1000)
                        codeload = 0x30000
                        triggerPixel = int("0x{}000".format(tpxl),16)
                        hexWrite = (intTrim | codeload | triggerPixel)
                        # value written here will be 0x3XYYY
                        # 3 specifies that this is a code n load n operation
                        # X specifies trigger ch/pxl as either 0,1,2,3 (in hex)
                        # YYY specifies the low side voltage in mV
                        logging.info( intTrim )
                        logging.info( module.WriteSetting("LowSideVoltage",hexWrite) )


def getTunedWrite(moduleID,FPM,module,Vped, numBlock=2):
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

        trimsToWrite = getTrims(moduleID,FPM)
        logging.info(trimsToWrite)
        logging.info(Vped)
        logging.info(Vofs1)
        logging.info(Vofs2)
        logging.info(PMTref4)


        setTrims(module, trimsToWrite)

        module.WriteSetting("NumberOfBlocks", numBlock-1)


        #return list of pmtref4 vals
        return PMTref4

if __name__ == "__main__":
        filename=sys.argv[1]
        readVals(filename)

