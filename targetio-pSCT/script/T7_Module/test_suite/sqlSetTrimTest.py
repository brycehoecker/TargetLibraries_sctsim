# Created by Colin Adams
# 3/11/2016

# Takes Vbias voltage for each trigger pixel and subtracts it from the hi side
# This gives trim voltage
# Each trigger pixel written with its trim voltage
import target_driver
import time
import pymysql

# needs module, 2 module dicts, and list of vtrim voltages (or alternatively, a list of vbias voltages)
def getTrims(FEE):
	#Vbiaslist = []

	nQuads = 100
	hiSide = 70.00 #V
	
	print FEE #YYY module ID

	# connect to MySQL
	sql = pymysql.connect(host='romulus.ucsc.edu', user='CTAreadonly', password='readCTAdb',database='CTAoffline')
	cursor = sql.cursor()

	# figure out the FPM from SQL 
	select_position = "SELECT sector, position FROM associations WHERE module=%(module)s"
	cursor.execute(select_position,{'module':FEE})
	FPM = cursor.fetchone()
	print FPM
	print FPM[1]

	# get quadrant associations for FPM
	select_quads = "SELECT q0, q1, q2, q3 FROM associations WHERE module=%(module)s"
	cursor.execute(select_quads,{'module':FEE})
	quads = cursor.fetchone()
	print quads

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
		trimsToWrite.append(quadtrims)
	
	cursor.close()
	sql.close()

	return trimsToWrite

def setTrims(module, trimsToWrite):
	nAsic = 4
	nTrgPxl = 4
	asicDict = {0 : 0b0001, 1 : 0b0010, 2 : 0b0100, 3 : 0b1000}
	trigPxlDict
	module.WriteSetting("HV_Enable", 0b1)
	module.WriteSetting("SelectLowSideVoltage",0b1)
	# selects all asics
	module.WriteSetting("HVDACControl",0b1111)
	# sets reference voltage for all asics to 4.096 V 
	module.WriteSetting("LowSideVoltage",0x73000)
	for asic in range(nAsic):
		module.WriteSetting("HVDACControl",asicDict[asic])
		for tpxl in range(nTrgPxl):
			# picks correct trim voltage from list, converts to mV, and converts that to hex
			intTrim = int(trimsToWrite[asic][tpxl]*1000)
			codeload = 0x30000
			triggerPixel = int("0x{}000".format(tpxl),16)
			hexWrite = (intTrim | codeload | triggerPixel)
			# value written here will be 0x3XYYY
			# 3 specifies that this is a code n load n operation
			# X specifies trigger ch/pxl as either 0,1,2,3 (in hex)
			# YYY specifies the low side voltage in mV
			print intTrim	
			print module.WriteSetting("LowSideVoltage",hexWrite)
				


if __name__ == "__main__":
	"""
	my_ip = "192.168.1.2"
	tb_ip = "192.168.1.173"
	board_ip = "192.168.0.173"

	board_def = ("/Users/pkarn/TargetDriver/config/"
	    "TM7_FPGA_Firmware0xFEDB0007.def")
	asic_def = "/Users/pkarn/TargetDriver/config/TM7_ASIC.def"

	board = target_driver.TargetModule(board_def, asic_def, 1)
	print board.EstablishSlowControlLink(my_ip, board_ip)
	#board.WriteSetting("SetSlowControlPort", 8201)
	#board.WriteSetting("SetDataPort", 8107)
	time.sleep(0.1)
	print board.Initialise()

	time.sleep(0.1)

	tester = target_driver.TesterBoard()
	print tester.Init(my_ip, tb_ip)
	time.sleep(0.1)
	tester.EnableReset(True)
	time.sleep(0.1)
	tester.EnableReset(False)
	time.sleep(0.1)
	"""
	
	moduleID = 100
	print getTrims(moduleID)

	"""
	board.CloseSockets()
	tester.CloseSockets()
	"""


