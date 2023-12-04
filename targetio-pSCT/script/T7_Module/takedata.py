import record
import run_control
import target_driver
import time
'''
#Establish connections and initialize
my_ip = "192.168.1.2"
tb_ip = "192.168.1.173"
board_ip = "192.168.0.173"

board_def = ("/Users/pkarn/TargetDriver/config/"
    "TM7_FPGA_Firmware0xFEDB0007.def")
asic_def = "/Users/pkarn/TargetDriver/config/TM7_ASIC.def"

fail = 0

board = target_driver.TargetModule(board_def, asic_def, 1)
fail |= board.EstablishSlowControlLink(my_ip, board_ip)
#board.WriteSetting("SetSlowControlPort", 8201)
#board.WriteSetting("SetDataPort", 8107)
time.sleep(0.1)
fail |= board.Initialise()

time.sleep(0.1)

tester = target_driver.TesterBoard()
fail |= tester.Init(my_ip, tb_ip)
time.sleep(0.1)
tester.EnableReset(True)
time.sleep(0.1)
tester.EnableReset(False)
time.sleep(0.1)
'''
fail = 0
if not fail:
#Set up output
    hostname = run_control.getHostName()
    outdirname = run_control.getDataDirname(hostname)
    runID = run_control.incrementRunNumber(outdirname)
    outFile = "%srun%d.fits" % (outdirname,runID)
    print "Writing to: %s" % outFile

#Take data
    record.record(outFile)
