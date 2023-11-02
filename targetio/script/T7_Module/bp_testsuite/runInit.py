import target_driver
import time
import numpy as np
import getSerial
import piCom
#import logging

std_my_ip = ["192.168.10.1"]
std_tb_ip = "dacq_wr0" ##"192.168.1.173"
std_board_ip = "192.168.10.109"
std_board_def = "/home/ctauser/TargetDriver/config/T7_M_FPGA_Firmware0xB0000107.def"
std_asic_def = "/home/ctauser/TargetDriver/config/T7_ASIC.def"
slot_dict={118:0x800, 125:0x1000, 126:0x2000, 101:0x4000, 119:0x20000, 108:0x40000, 115:0x40000, 121:0x80000, 116:0x80000, 110:0x100000, 128:0x800000, 123:0x1000000, 124:0x2000000, 112:0x4000000, 100:0x10000000, 111:0x20000000, 114:0x40000000, 107:0x80000000}

currentPowerVal=0

def powerModule(moduleID, pi, currentPowerVal, on=1):
		if(on):
			currentPowerVal+=slot_dict[moduleID]
		else:
			if(currentPowerVal>0):
				currentPowerVal-=slot_dict[moduleID]
			else:
				currentPowerVal=0

		powerVal=currentPowerVal
		print(hex(powerVal))
		piCom.powerFEE(pi, str(hex(powerVal)))
		time.sleep(0.5)
		return currentPowerVal


#std_board_def = "/Users/colinadams/TargetDriver/config/TM7_FPGA_Firmware0xB0000100.def"
#std_board_def = "/Users/colinadams/TargetDriver/config/T7_M_FPGA_Firmware0xB0000102.def"
#std_asic_def = "/Users/colinadams/TargetDriver/config/T7_ASIC.def"

def Init(pi, my_ip=std_my_ip, tb_ip=std_tb_ip, board_ipList=[std_board_ip],board_def=std_board_def,asic_def=std_asic_def, ourModuleIDList=[1]):

	currentPowerVal=0
	for mid in ourModuleIDList:
		currentPowerVal = powerModule(mid, pi, currentPowerVal, 1)

	time.sleep(20)


	print "%s %s" % (board_def, asic_def)
	moduleList=[]
	trialCount=0
	for i in range( len(ourModuleIDList) ):
		# integer value set to define module
		moduleList.append( target_driver.TargetModule(board_def, asic_def,i) )
		subnet = int(board_ipList[i].strip().split('.')[2])
		selectMyIp=0
		if(subnet-10==0):
			selectMyIp=0
		elif(subnet-10==2):
			selectMyIp=1
		elif(subnet-10==4):
			selectMyIp=2

		print "My IP is: ", my_ip[selectMyIp], "for module: ", ourModuleIDList[i], ", with boardIP: ", board_ipList[i]
		failure = moduleList[i].EstablishSlowControlLink(my_ip[selectMyIp], board_ipList[i])
		
		trialCount=0
		while(trialCount<2 and failure):
			print "******* Initial communications try failed, the module will be powercycled for a next attempt.*****************"
			currentPowerVal = powerModule(ourModuleIDList[i], pi, currentPowerVal, 0)
			time.sleep(2)
			currentPowerVal = powerModule(ourModuleIDList[i], pi, currentPowerVal, 1)
			time.sleep(25)
			trialCount+=1
			failure = moduleList[i].EstablishSlowControlLink(my_ip[selectMyIp], board_ipList[i])

		if(failure):
			print "Failed to establish slow control connection, with:", failure
			#logging.error("Failed to establosh slow control connection, with: %d", failure)
			return failure, moduleList
		else:
			port = np.uint16(0)
			dataPort = np.uint16(0)
			regVal = 0 
			time.sleep(0.2)
			regVal = moduleList[i].ReadRegister(0x80)
			port = (regVal[1] >> 16) & 0xFFFF
			dataPort = (regVal[1]) & 0xFFFF
			print "Slow control connection established with slow control port:", port, "and data port:", dataPort
		        address = 0x02  # LSW of serial code
		        hexLSW = getSerial.queryBoard(moduleList[i],address)
		        address = 0x03  # MSW of serial code
		        hexMSW = getSerial.queryBoard(moduleList[i],address)
		        serialCode = "%s%s" % (hexMSW,hexLSW[2:10])
			print "The module serial number is:", serialCode
			
			# integer values to identify modules
    			moduleList[i].WriteSetting("DetectorID", i)
			time.sleep(1 + 2.0*(i%4==5))

			#logging.info("Slow control connection established.")
	#board.WriteSetting("SetSlowControlPort", 8201)
	#board.WriteSetting("SetDataPort", 8107)
	time.sleep(1)
##	failure = module.Initialise()
	#module.WriteSetting("SoftwareReset", 0xBECEDACE)
##	module.EnableDLLFeedback()
	


	print "The states are: 1=Safe, 2=PreSync, 3=Ready"
	for module in moduleList:
		state =	module.GetState()
		print "Module state:", state
		time.sleep(0.2)

		TC_OK = module.GoToPreSync()
		print "Module into PreSync with return: ", TC_OK

		time.sleep(0.2)
		state =	module.GetState()
		time.sleep(0.2)
		print "Module state:", state
	

	fail=1
	while(fail ):
		time.sleep(1)
#		stat1 = module.GoToReady()
		print "SYNCING NOW!"
		piCom.sendSync(pi)
#		time.sleep(0.1)
#		piCom.sendSync(pi)
#		time.sleep(0.1)
#		time.sleep(0.1)
#		piCom.sendSync(pi)
#		time.sleep(0.3)
#		piCom.sendSync(pi)
		time.sleep(1)
		fail=0
		print "Trying to go to ready"
		for module in moduleList:
			failSingle = module.GoToReady()
			print "Failed:?", failSingle
			if(failSingle!=0):
				fail=1
			time.sleep(0.5)
		if(fail==1): "FAILED! - Repeat"
			
	for module in moduleList:	
		state = module.GetState()
		print "Module state:", state
	
	
	print "Module succesfully initialized."






#	print "wait for backplane setup"
#	time.sleep(30)
#	print "Stop backplane setup!"
	return failure, moduleList


def Close(moduleList):
	for module in moduleList:
		module.CloseSockets()
	

if __name__ == "__main__":
	Init()
