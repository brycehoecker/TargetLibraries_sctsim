#!/usr/bin/env python
import runInit
import powerCycle
import pymysql

# dict stores module associations via ('hex string':'serial #') 
moduleDict = {'0x9700001798848301':'128','0xb20000179889bc01':'126','0x0700001798717a01':'125','0x7c00001798917201':'124','0xf000001798986d01':'123','0xc1000017978ee501':'121','0x2100001797902d01':'118','0xc6000017979df701':'116','0xbd00001797a49d01':'114','0x28000017979d5101':'100','0xe000001798945901':'101','0x76000017978e4001':'107','0x0c00001798677f01':'111','0x15000017978fb401':'108','0x61000017978b1501':'113','0x1300001798806501':'110','0x98000017987f2401':'112','0xe4000017979a8201':'119'}

def getSerial(outHex=False):
        #power cycle at beginning so the tester board is initialized
        bps = powerCycle.powerCycle()
        module, tester = runInit.Init()

        #Determine which module we are running on
        address = 0x02  # LSW of serial code
        hexLSW = queryBoard(module,address)
        address = 0x03  # MSW of serial code
        hexMSW = queryBoard(module,address)
        serialCode = "%s%s" % (hexMSW,hexLSW[2:10])
        
        runInit.Close(module, tester)
        powerCycle.powerOff(bps)
        
        FPM = querySQL(moduleDict[serialCode])

        #Enable outHex so that the FEE serial # will be returned instead
        #Use to add new modules to the dictionary
        if outHex:
                return serialCode

        return moduleDict[serialCode], FPM 

# reads registers 0x2 and 0x3 for 2 hex strings - used to identify FEE ID
def queryBoard(tester,address):
        hexAddress = "0x%02x" % address
        ret, value = tester.ReadRegister(address)
        hexValue = "0x%08x" % value
        
        return hexValue

def querySQL(moduleID):
        # connect to MySQL
        sql = pymysql.connect(host='romulus.ucsc.edu', user='CTAreadonly', password='readCTAdb',database='CTAoffline')
        cursor = sql.cursor()

        # figure out the FPM from SQL 
        select_position = "SELECT sector, position FROM associations WHERE module=%(module)s"
        cursor.execute(select_position,{'module':moduleID})
        FPM = cursor.fetchone()
        
        cursor.close()
        sql.close()

        return FPM

# if module hasn't been added, get its serial # by running the script as a standalone
if __name__ == "__main__":
        print(getSerial(False))
