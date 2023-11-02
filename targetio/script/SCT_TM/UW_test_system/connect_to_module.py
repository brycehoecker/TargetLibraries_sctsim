import target_driver
import target_io
import time
#from astropy.io import ascii
import os
import sys
import random
import datetime
import numpy as np
#Wisconsin specific modules:
time.sleep(5)

raw_input("Is the module properly powered?")

timestamp = time.time()
dataset = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M')
baseDir = dataset+'/'
#baseDir = "/Users/tmeures/target5and7data/testData2019/module3/TARGETCTesting/"+dataset+'/'
try:
		os.mkdir(baseDir)
		os.chmod(baseDir, 0o777)
except:
		print "directory", baseDir, "already exists."

my_ip = "192.168.12.1"
module_ip = "192.168.12.173"
initialize = True

homedir = os.environ['HOME']

module_def = homedir+"/svn_folder/CCC/TargetDriver/branches/issue37423/config/SCT_MSA_FPGA_Firmware0xC0000002.def"
asic_def = homedir+"/svn_folder/CCC/TargetDriver/trunk/config/TC_ASIC.def"
trigger_asic_def = homedir+"/svn_folder/CCC/TargetDriver/trunk/config/T5TEA_ASIC.def"

module = target_driver.TargetModule(module_def, asic_def, trigger_asic_def, 0)
if initialize:
    module.EstablishSlowControlLink(my_ip, module_ip)
    module.Initialise()
    module.EnableDLLFeedback()
    print ("module initialized")
else:
    module.ReconnectToServer(my_ip, 8201, module_ip, 8105)

ret, fw = module.ReadRegister(0)
print ("Firmware version: {:x}".format(fw))


module.CloseSockets()

