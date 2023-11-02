#!/usr/bin/env python
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
## fix default daq values before turning off testing mode
#defaults = {
#        "nblocks": 8,
#        "packets":8,
#        "daq_time": 10.,
#        "triggerdelay": 500,
#        "triggertype": 1,
#        "vped": 1200,
#        "vpedstart": 100,
#        "vpedstop": 4000,
#        "vpedstep": 100,
#}

def exec_pedestal(args):
        moduleID = int(args.module)
        vpedscan = args.vpedscan
        disable_analysis = args.disable_analysis
        disable_datataking = args.disable_datataking
        ch0 = int(args.channel0)
        nch = int(args.nchannels)
        ret = 0
        force = args.force
        if testing_mode:
                nblocks = int(args.nblocks)
                packets = int(args.packets)
                daq_time = args.length
                triggerdelay = int(args.triggerdelay)
                triggertype = args.triggertype 
                vped=int(args.vped) 
                sst = 58 # standard value
                vtrim=1240 # standard value
                vpedvals=args.vpedvals
                if len(vpedvals)>2:
                        vpedstart = vpedvals[0]
                        vpedstop = vpedvals[1]
                        vpedstep = vpedvals[2]
                elif len(vpedvals)==2:
                        vpedstart = vpedvals[0]
                        vpedstop = vpedvals[1]
                        vpedstep = 100
                elif len(vpedvals)==1:
                        vpedstart = 100
                        vpedstop = vpedvals[0]
                        vpedstep = 100
                        
        else:
                nblocks = defaults["nblocks"]
                packets = defaults["packets"]
                daq_time = defaults["daq_time"]
                triggerdelay = defaults["triggerdelay"]
                triggertype = defaults["triggertype"]
                vped = defaults["vped"]
                vpedstart = defaults["vpedstart"]
                vpedstop = defaults["vpedstop"]
                vpedstep = defaults["vpedstep"]


        fast_mode = args.fast_mode

        if vpedscan:
                vpeds = range(vpedstart,vpedstop,vpedstep)
        else:
                vpeds = [vped]
        outfiles = []

        outdir = args.outdir+"/"
        if testing_mode:
                outdir += "testing/"
        outdir += "Module"+str(moduleID)
        #outdir += "Module"+str(moduleID)+"_191008/"
        if args.moduletag!="":
                outdir += "_"+args.moduletag
        outdir += "/"
        os.system("mkdir -p "+str(outdir))
        

        for _vp in vpeds:
                outfile = outdir+"/"+args.outname
                if triggertype==1:
                        outfile+="_exttrigger"
                elif triggertype==2:
                        outfile+="_hardsync"
                #outfile+="_nblocks"+str(nblocks)+"_packets"+str(packets)+"_vped"+str(_vp)+"_delay"+str(triggerdelay)+"_r0.tio"
                outfile+="_nblocks"+str(nblocks)+"_packets"+str(packets)+"_vped"+str(_vp)+"_r0.tio"
                #print("Output file:", outfile)
                logger.info("Output file: "+outfile)
                outfiles.append(outfile)
                
                if not disable_datataking:
                        if os.path.exists(outfile):
                                os.system("rm "+outfile)
                        #logger.info("Taking data")
                        take_pedestal(outfile, nblocks=nblocks, packets=packets, daq_time=daq_time, triggerdelay=triggerdelay, vped=_vp, sst=sst, vtrim=vtrim, triggertype=triggertype )
                        force=True ## if new data were taken force the calculation of pedestal database and calibrated file
                        #logger.log(logger.TEST_LEVEL_INFO, "Finished pedestal data taking.")

                if not disable_analysis:
                        #logger.log(logger.TEST_LEVEL_INFO, "Starting pedestal analysis.")

                        ### calibration
                        peddbfile = generate_ped(outfile, force=force)
                        outfile_r1 = apply_calibration(outfile, peddbfile, force=force)

                        ## add analysis here
                        analysis_dir = outfile.replace("_r0.tio","")+"/"
                        os.system("mkdir -p "+str(analysis_dir))

                        ## run_analysis
                        ret = analyse_pedestal(outfile, outfile_r1, fname_ped=peddbfile, outdir=analysis_dir, ch0=ch0, nch=nch, tag="", fast=fast_mode)
                        #logger.log(logger.TEST_LEVEL_INFO, "Finished pedestal analysis.")

        ## summary for Vped scan
        if len(vpeds)>1 and not args.disable_summary:
                # read results : average_ped vs vped, noise (avg, per chan) vs vped
                # do plots/fit
                logger.log(logger.TEST_LEVEL_INFO, "Starting summary analysis")
                plotdir = outdir+"/vpedscan_summary_plot/"
                os.system("mkdir -p "+plotdir)
                ret = do_pedestal_plots(outfiles,vpeds, plotdir, chlist=range(ch0,ch0+nch))
                logger.log(logger.TEST_LEVEL_INFO, "Finished summary analysis.")

        return ret

if __name__=="__main__":
        ## example usage:
        ## ./run_pedestal.py -m 1 -t 1 -b 2 -v 1200 -d 500 -l 10
        '''
        parser = argparse.ArgumentParser()
        parser.add_argument("-m" ,"--module", help="Module ID", type=int, default=0)
        parser.add_argument("-mt" ,"--moduletag", help="tag to be appended to output folder", type=str, default="")
        parser.add_argument("-o" ,"--outname", help="output name to be prepended to the output file name", type=str, default="pedestal")
        parser.add_argument("-D" ,"--outdir", help="output directory path where to save data", type=str, default="./")
        parser.add_argument("-v" ,"--vpedscan", help="activate vped scan", action="store_true")
        parser.add_argument("-da" ,"--disable-analysis", help="flag to disable analysis", action="store_true")
        parser.add_argument("-dt" ,"--disable-datataking", help="flag to disable datataking", action="store_true")
        parser.add_argument("-c" ,"--channel0", help="channel from which the analysis starts", type=int, default=0)
        parser.add_argument("-n" ,"--nchannels", help="number of channels to be analyzed starting from channel specified with -c option", type=int, default=64)

        if testing_mode:
                parser.add_argument("-vp" ,"--vped", help="Vped to use", type=int, default=1200)
                parser.add_argument("--vpedvals", help="provide start, stop and step values vped scan", nargs="+", type=int, default=[4000])
                parser.add_argument("-b" ,"--nblocks", help="number of Blocks of 32 samples", type=int, default=8)
                parser.add_argument("-p" ,"--packets", help="number of packets per event", type=int, default=8)
                parser.add_argument("-l" ,"--length", help="acquisition time in seconds, ignored for hardsync pedestal", type=float, default=10)
                parser.add_argument("-t" ,"--triggertype", help="trigger type: 0=internal, 1=external, 2=hardsync", type=int, default=1)
                parser.add_argument("-d" ,"--triggerdelay", help="trigger delay", type=int, default=500)
        '''                
        parser = init_parser(key="pedestal")
        args = parser.parse_args()
        #print(args)
        outdir = get_outdir(args)
        #global logger
        #logger = LoggerWriter(logname="Pedestal", logfile=unique_filename(outdir+"/pedestal.log"))
        logger.setup(logname="Pedestal", logfile=unique_filename(outdir+"/pedestal.log"), debug_mode = args.debug)

        svn_ver, cmd = get_info()
        logger.log(logger.TEST_LEVEL_INFO, "SVN revision: "+svn_ver)
        logger.log(logger.TEST_LEVEL_INFO, "Running command: "+cmd)

        result = exec_pedestal(args)
        if (result == 0): logger.log(logger.TEST_LEVEL_PASS,"Finished working on pedestal.")
        else: logger.log(logger.TEST_LEVEL_FAIL,"Failure while working on pedestal.")
