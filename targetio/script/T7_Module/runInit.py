import target_driver
import time

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

#board.CloseSockets()
#tester.CloseSockets()
