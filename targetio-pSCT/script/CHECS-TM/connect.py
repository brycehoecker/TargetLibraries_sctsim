import target_driver
import target_io
import time

outfile = "!/home/cta/luigi/CHECS-TM/data/20170424/test_dump.fits"
my_ip = "192.168.12.1"
module_ip = "192.168.12.173"
initialize = True



module_def = "/home/cta/Software/TargetDriver/branches/issue14151/config/TC_MSA_FPGA_Firmware0xC0000003.def"
asic_def = "/home/cta/Software/TargetDriver/branches/issue14151/config/TC_ASIC.def"
trigger_asic_def = "/home/cta/Software/TargetDriver/branches/issue14151/config/T5TEA_ASIC.def"


module = target_driver.TargetModule(module_def, asic_def, trigger_asic_def, 0)
returnCode = module.EstablishSlowControlLink(my_ip, module_ip)
print("return code: ", returnCode)
