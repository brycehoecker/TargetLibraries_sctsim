import target_driver
import time
#import logging

std_my_ip = "192.168.10.1"
std_tb_ip = "192.168.1.173"
std_board_ip = "192.168.10.101"
std_board_def = "T7_M_FPGA_Firmware0xB0000107.def"
std_asic_def = "/Users/tmeures/TargetDriver/config/T7_ASIC.def"

#std_board_def = "/Users/colinadams/TargetDriver/config/TM7_FPGA_Firmware0xB0000100.def"
#std_board_def = "/Users/ltaylor/TargetDriver_new/config/T7_M_FPGA_Firmware0xB0000102.def"
#std_asic_def = "/Users/ltaylor/TargetDriver_new/config/T7_ASIC.def"

def Init(my_ip=std_my_ip,tb_ip=std_tb_ip,board_ip=std_board_ip,board_def=std_board_def,asic_def=std_asic_def):
	board = target_driver.TargetModule(board_def, asic_def, 1)
	failure = board.EstablishSlowControlLink(my_ip, board_ip)
	if(failure):
		print("Failed to establosh slow control connection, with:", failure)
		#logging.error("Failed to establosh slow control connection, with: %d", failure)
	else:
		print("Slow control connection established.")
		#logging.info("Slow control connection established.")
	#board.WriteSetting("SetSlowControlPort", 8201)
	#board.WriteSetting("SetDataPort", 8107)
	time.sleep(0.1)
	failure = board.Initialise()
	if(failure):
		print("Failed to initialize module, with:", failure)
	else:
		print("Module succesfully initialized.")
	
	time.sleep(0.1)

	tester = target_driver.TesterBoard()
	failure = tester.Init(my_ip, tb_ip)
	if(failure):
		print("Failed to initialize tester board, with:", failure)
	else:
		print("Tester board succesfully initialized.")
	time.sleep(0.1)
	tester.EnableReset(True)
	time.sleep(0.1)
	tester.EnableReset(False)
	time.sleep(0.1)
	
	#board.CloseSockets()
	#tester.CloseSockets()
	
	return board, tester


def Close(module, tester):
	module.CloseSockets()
	tester.CloseSockets()
	

if __name__ == "__main__":
	Init()
