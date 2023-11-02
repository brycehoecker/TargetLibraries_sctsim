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
from Peltier_utils import *
from MyLogging import logger


def exec_peltier(args):
        moduleID = int(args.module)

        outdir = args.outdir+"/"
        if testing_mode:
                outdir += "testing/"
        outdir += "Module"+str(moduleID)
        if args.moduletag!="":
                outdir += "_"+args.moduletag
        outdir += "/"
        os.system("mkdir -p "+str(outdir))

        outfilename = "peltier"

        target_ip = "192.168.12.173"
        # Take data:
        if not args.disable_datataking:
                do_peltier(outdir, target_host=target_ip)
                # Results are now stored in peltier.yaml file

        fail = 0
        # Analyze data saved in the voltages.yaml file:
        fail = analyse_peltier(
            out_dir=outdir,
            peltier_file="peltier.yaml",
            limits_file="./limits.yaml"
        )

        return int(fail)

if __name__=="__main__":
        ## example usage:
        ## ./run_power.py -m 1 -mt 20200724
        parser = init_parser(key="peltier")
        args = parser.parse_args()
        outdir = get_outdir(args)
        logger.setup(logname="Peltier", logfile=unique_filename(outdir+"/peltier.log"), debug_mode = args.debug)

        svn_ver, cmd = get_info()
        logger.log(logger.TEST_LEVEL_INFO, "SVN revision: "+svn_ver)
        logger.log(logger.TEST_LEVEL_INFO, "Running command: "+cmd)

        result = exec_peltier(args)
        if (result == 0): logger.log(logger.TEST_LEVEL_PASS,"Finished working on peltier.")
        else: logger.log(logger.TEST_LEVEL_FAIL,"Failure while working on peltier.")

