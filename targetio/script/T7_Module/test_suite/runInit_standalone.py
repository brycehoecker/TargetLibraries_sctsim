import target_driver
import time
#import logging

std_my_ip = "192.168.10.1"
std_tb_ip = "192.168.1.173"
std_board_ip = "192.168.10.101"
std_board_def = "T7_M_FPGA_Firmware0xB0000107.def"
std_asic_def = "/Users/ltaylor/TargetDriver_new/config/T7_ASIC.def"


def Init(my_ip=std_my_ip,tb_ip=std_tb_ip,board_ip=std_board_ip,board_def=std_board_def,asic_def=std_asic_def):
	board = target_driver.TargetModule(board_def, asic_def, 1)
	failure = board.EstablishSlowControlLink(my_ip, board_ip)
	if(failure):
		print "Failed to establosh slow control connection, with:", failure
	else:
		print "Slow control connection established."
	time.sleep(0.1)
	failure = board.Initialise()
	if(failure):
		print "Failed to initialize module, with:", failure
	else:
		print "Module succesfully initialized."
	
	board.EnableDLLFeedback()


	time.sleep(0.1)

	return board


def Close(module):
	module.CloseSockets()
	

if __name__ == "__main__":
	Init()
