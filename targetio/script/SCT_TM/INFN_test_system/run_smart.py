#!/usr/bin/env python
import logging
import target_driver
import target_io
import time
from astropy.io import ascii
import os,sys
import argparse

from TC_utils import *
from TC_analysis_utils import *
from utils import *
from MyLogging import logger



#testing_mode = True

fast_mode = False
#fast_mode = True


def exec_smart_calib(args):
    logger.info("run_smart called with the following parameters: " + str(args))
    moduleID = int(args.module)
    disable_analysis = args.disable_analysis
    disable_datataking = args.disable_datataking
    #ch0 = int(args.channel0)
    #nch = int(args.nchannels)
    #force = args.force
    ret = 0
    smart_dacs=args.smart_dacs
    if type(smart_dacs) is list and len(smart_dacs)==1:
        smart_dacs = smart_dacs[0]
    smart_global=args.smart_global



    outdir = args.outdir+"/"
    if testing_mode:
        outdir += "testing/"
    outdir += "Module"+str(moduleID)
    if args.moduletag!="":
        outdir += "_"+args.moduletag
    outdir += "/"
    os.system("mkdir -p "+str(outdir))

    outfile = outdir+"/"+args.outname
    outfile += "_SMART_{0}_{1}_{2}".format(smart_global[0],smart_global[1],smart_global[2])
    if type(smart_dacs) is not list:
        outfile += "_DAC{0}".format(smart_dacs)

    if not disable_datataking:
        do_calib_smart(smart_dacs=smart_dacs,smart_global=smart_global, outfilename=outfile)
    if not disable_analysis:
        ret = analyse_smart_calib(outdir, os.path.basename(outfile), limits_file="./limits.yaml")
        
    return ret





if __name__=="__main__":
    ## example usage:
    ## ./run_signal.py -module 1 -t 1 -b 2 -v 1200 -d 500 -l 10
    parser = init_parser(key="smart")
    args = parser.parse_args()
    outdir = get_outdir(args)
    logger.setup(logname="Smart", logfile=unique_filename(outdir+"/smart.log"), debug_mode = args.debug)
    
    svn_ver, cmd = get_info()
    logger.log(logger.TEST_LEVEL_INFO, "SVN revision: "+svn_ver)
    logger.log(logger.TEST_LEVEL_INFO, "Running command: "+cmd)

    #update_global_connection_details(my_ip=dval["global"].get("my_ip"),module_ip=dval["global"].get("module_ip"),
    #                                 asic_def=dval["global"].get("tc_def"),trigger_asic_def=dval["global"].get("t5tea_def"),
    #                                 module_def=dval["global"].get("fpga_def"))
    update_global_connection_details(asic_def="/home/leonardo/Software/TARGET/TargetDriver/trunk/config/TC_ASIC.def",
                                     trigger_asic_def="/home/leonardo/Software/TARGET/TargetDriver/trunk/config/T5TEA_ASIC.def",
                                     module_def="/home/leonardo/Software/TARGET/firmware_smart/SCT_MSA_FPGA_Firmware0xC0000009.def")

    result = exec_smart_calib(args)
    if (result == 0): logger.log(logger.TEST_LEVEL_PASS,"Finished working on SMART.")
    else: logger.log(logger.TEST_LEVEL_FAIL,"Failure while working on SMART.")
