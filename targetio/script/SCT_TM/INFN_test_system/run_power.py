#!/usr/bin/env python
import target_driver
import target_io
import time
from astropy.io import ascii
import os,sys
import argparse
import yaml
import enlighten


from TC_utils import *
from TC_analysis_utils import *
from utils import *
from MyLogging import logger

def exec_power(args):
        moduleID = int(args.module)

        outdir = args.outdir+"/"
        if testing_mode:
                outdir += "testing/"
        outdir += "Module"+str(moduleID)
        #outdir += "Module"+str(moduleID)+"_191008/"
        if args.moduletag!="":
                outdir += "_"+args.moduletag
        outdir += "/"
        os.system("mkdir -p "+str(outdir))

        outfilename = "voltages"
        
        # Take data:
        if not args.disable_datataking:
                do_power(outdir=outdir)
                # Results are now stored in voltages.yaml file

        # Analyze data saved in the voltages.yaml file:
        fail, dstatus = analyse_power(
            out_dir=outdir,
            voltages_file="voltages.yaml",
            limits_file="./limits.yaml"
        )

        return fail, dstatus
        

if __name__=="__main__":
        ## example usage:
        ## ./run_power.py -m 1 -mt 20200724
        parser = init_parser(key="power")
        args = parser.parse_args()
        outdir = get_outdir(args)
        logger.setup(logname="Power", logfile=unique_filename(outdir+"/power.log"), debug_mode = args.debug)

        svn_ver, cmd = get_info()
        logger.log(logger.TEST_LEVEL_INFO, "SVN revision: "+svn_ver)
        logger.log(logger.TEST_LEVEL_INFO, "Running command: "+cmd)

        result, _ = exec_power(args)
        if (result == 0): logger.log(logger.TEST_LEVEL_PASS,"Finished working on power.")
        else: logger.log(logger.TEST_LEVEL_FAIL,"Failure while working on power.")

