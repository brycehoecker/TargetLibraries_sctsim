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
from agilent33250A_inverted import *  ## TO BE REMOVED

#testing_mode = True

#fast_mode = False
fast_mode = True

## fix default daq values before turning off testing mode
#defaults = {
#        "nblocks": 8,
#        "packets": 8,
#        "daq_time": 10.,
#        "triggerdelay": 500,
#        "triggertype": 1,
#        "vped": 1200,
#        "sigstart": 0,
#        "sigstop": 0.3,
#        "sigstep": 0.05,
#        "sigfreq": 1113,
#}

#cmd_agilent = "./agilent33250A.sh {0} {1}" #"/home/target5/test.sh {0} {1}" # <ampiezza segnale in V> <frequenza in Hz>
####cmd_agilent = "./agilent33250A_inverted.py {0:.4f} {1}" 


def exec_signal_sipm(args):
        logger.info("run_signal called with the following parameters: " + str(args))
        moduleID = int(args.module)
        signalscan = args.signalscan
        disable_analysis = args.disable_analysis
        disable_datataking = args.disable_datataking
        ch0 = int(args.channel0)
        nch = int(args.nchannels)
        force = args.force
        nbad_ch = 0
        if testing_mode:
                nblocks = int(args.nblocks)
                packets = int(args.packets)
                daq_time = args.length
                triggerdelay = int(args.triggerdelay)
                triggertype = args.triggertype 
                vped=int(args.vped) 
                sst = 58 # standard value
                vtrim=1240 # standard value
                #signalvals=args.signalvals
                #sigfreq=args.signalfreq
                signalvals=[10,100,50]#args.signalvals
                sigfreq=1000#args.signalfreq
                if len(signalvals)>2:
                        sigstart = signalvals[0]
                        sigstop = signalvals[1]
                        sigstep = signalvals[2]
                elif len(signalvals)==2:
                        sigstart = signalvals[0]
                        sigstop = signalvals[1]
                        sigstep = 0.1
                elif len(signalvals)==1:
                        sigstart = 0.
                        sigstop = signalvals[0]
                        sigstep = 0.1

        else:
                nblocks = defaults["nblocks"]
                packets = defaults["packets"]
                daq_time = defaults["daq_time"]
                triggerdelay = defaults["triggerdelay"]
                triggertype = defaults["triggertype"]
                vped = defaults["vped"]
                sigstart = defaults["sigstart"]
                sigstop = defaults["sigstop"]
                sigstep = defaults["sigstep"]
                sigfreq = defaults["sigfreq"]

        pmtref4 = args.pmtref4
        thresh = args.thresh
        enable_HV=args.enable_hv
        disable_smart_channels=args.disable_smart_channels
        smart_dacs=args.smart_dacs
        smart_global=args.smart_global
        smart_flag_dacs=args.smart_flag_dacs
        smart_flag_globals=args.smart_flag_globals 
        if type(smart_dacs) is list and len(smart_dacs)==1:
                smart_dacs = smart_dacs[0]
        #dacs_tag="DAC"
        #if type(smart_dacs) is not list:
        #        dacs_tag+="_"+str(smart_dacs)
        #else:
        #        dacs_tag+="_list"
        
        if signalscan:
                cmd_list = []
                tag_list = []
                #for _sigamp in np.arange(sigstart,sigstop,sigstep):
                #        #cmd_list.append(cmd_agilent.format(_sigamp, sigfreq))
                #        cmd_list.append([_sigamp, sigfreq])
                #        tag_list.append("_signal{0:.4f}".format(_sigamp))
                #        #tag_list.append("_signal"+str(_sigamp))
                if smart_flag_globals:
                        for sg in smart_global:
                                tag_list.append("_SMART_{0}_{1}_{2}_DAC_{3}".format(sg[0],sg[1],sg[2],smart_dacs))
                                cmd_list.append([sg,smart_dacs])
                if smart_flag_dacs:
                        for dac in smart_dacs:
                                tag_list.append("_SMART_{0}_{1}_{2}_DAC_{3}".format(smart_global[0],smart_global[1],
                                                                                    smart_global[2],dac))
                                cmd_list.append([smart_global,dac])
        else:
                cmd_list = [[smart_global,smart_dacs]]
                tag_list = ["_SMART_{0}_{1}_{2}_DAC_{3}".format(smart_global[0],smart_global[1],smart_global[2],smart_dacs)]
                
        outdir = args.outdir+"/"
        if testing_mode:
                outdir += "testing/"
        outdir += "Module"+str(moduleID)
        if args.moduletag!="":
                outdir += "_"+args.moduletag
        outdir += "/"
        os.system("mkdir -p "+str(outdir))

        ## define pedestal file
        pedfile = outdir+"/"+args.pedname

        if args.pedtrigtype==1:
          pedfile+="_exttrigger"
        elif args.pedtrigtype==2:
          pedfile+="_hardsync"
        elif args.pedtrigtype==0:
          pedfile+="_inttrigger"
        else:
          raise ValueError("Incompatible value for pedestal trigger type. Only 0,1,2 accepted.")       
        #pedfile+="_nblocks"+str(nblocks)+"_packets"+str(packets)+"_vped"+str(vped)+"_delay"+str(triggerdelay)+"_r0.tio"
        ## new pedfile name

        pedfile+="_nblocks"+str(nblocks)+"_packets"+str(packets)+"_vped"+str(vped)+"_r0.tio"
        if not disable_analysis:
                if args.peddatabase is None:
                        peddbfile = generate_ped(pedfile, force=force)
                else:
                        peddbfile = args.peddatabase


        ## create command list
        outfile_list = []
        for cmd,tag in zip(cmd_list,tag_list):
                outfile = outdir+""+args.outname
                if enable_HV:
                        outfile+="_HV"
                if triggertype==1:
                        outfile+="_exttrigger"
                elif triggertype==2:
                        outfile+="_hardsync"
                elif triggertype==0:
                        outfile+="_inttrigger"

                outfile += tag
                       
                outfile+="_nblocks"+str(nblocks)+"_packets"+str(packets)+"_vped"+str(vped)+"_delay"+str(triggerdelay)+"_r0.tio"
                logger.info("Output file: " + outfile)
                outfile_list.append(outfile)

        ## take data
        if not disable_datataking:
                force=True
                if signalscan and fast_mode:
                        logger.log(logger.TEST_LEVEL_INFO,"Taking data in multiple runs")
                        loop_take_data_sipm(outfile_list, smart_globals=smart_global, nblocks=nblocks, packets=packets, daq_time=daq_time, triggerdelay=triggerdelay, vped=vped, sst=sst, vtrim=vtrim, triggertype=triggertype, triggermask=0xffff, pmtref4=pmtref4, thresh=thresh, enable_HV=enable_HV, disable_smart_channels=disable_smart_channels, smart_dacs=smart_dacs,smart_loop_globals=smart_flag_globals, smart_loop_dacs=smart_flag_dacs)
                else:
                        for cmd,outfile in zip(cmd_list,outfile_list):
                                if os.path.exists(outfile):
                                        os.system("rm "+outfile)
                                if signalscan:
                                        #result = agilent33250A_inverted(cmd[0], cmd[1], 0) ## TO BE CHANGED
                                        #if result != 0: raise ValueError("Could not set pulse amplitude")
                                        ### do something here to set the signal amplitude
                                        #logger.info(cmd)
                                        ####rrr = input("Are you sure the command is correct? (y/n)")
                                        #rrr = 'y'
                                        #if rrr=='y':
                                        #        os.system(cmd) ## scommentare dopo aver verificato che funzioni!
                                        #        pass
                                        pass
                                #logger.log(logger.TEST_LEVEL_INFO,"Taking data")
                                take_data_sipm(outfile, nblocks=nblocks, packets=packets, daq_time=daq_time, triggerdelay=triggerdelay, vped=vped, sst=sst, vtrim=vtrim, triggertype=triggertype, triggermask=0xffff, pmtref4=pmtref4, thresh=thresh, enable_HV=enable_HV, disable_smart_channels=disable_smart_channels, smart_dacs=cmd[1], smart_global=cmd[0] )
                logger.log(logger.TEST_LEVEL_INFO,"End of signal acquisition.")

        if not disable_analysis:
                i_outfile=0
                for outfile in outfile_list:
                        i_outfile+=1
                        logger.log(logger.TEST_LEVEL_MESS,"Step: {0}/{1}".format(i_outfile,len(outfile_list)))
                        #logger.log(logger.TEST_LEVEL_INFO, "Starting signal analysis.")
                        ### calibration
                        if args.peddatabase is None:
                                peddbfile = generate_ped(pedfile, force=force)
                        else:
                                peddbfile = args.peddatabase
                        outfile_r1 = apply_calibration(outfile, peddbfile, force=force)

                        ## add analysis here
                        analysis_dir = outfile.replace("_r0.tio","")+"/"
                        os.system("mkdir -p "+str(analysis_dir))

                        ## run_analysis
                        nbad_ch = analyse_signal(outfile_r1, fname_r0=outfile, outdir=analysis_dir, ch0=ch0, nch=nch, tag="", pulse_analysis=smart_flag_globals, dac_analysis=smart_flag_dacs)
                        #logger.log(logger.TEST_LEVEL_INFO,"Finished signal analysis.")

        if signalscan:
                # read results : average_ped vs vped, noise (avg, per chan) vs vped
                # do plots/fit
                logger.log(logger.TEST_LEVEL_INFO, "Starting summary analysis.")
                plotdir = outdir+"/linearity_summary_plots/"
                os.system("mkdir -p "+plotdir)
                #nbad_ch = do_signal_plots(outfile_list,np.arange(sigstart,sigstop,sigstep) , plotdir, chlist=range(ch0,ch0+nch))
                logger.log(logger.TEST_LEVEL_INFO, "Finished summary analysis.")
                if smart_flag_globals:
                        nbad_ch = do_sipm_plots(outfile_list, smart_global, plotdir, chlist=range(ch0,ch0+nch))
                elif smart_flag_dacs:
                        do_dacs_plots(outfile_list,smart_dacs,plotdir,chlist=range(ch0,ch0+nch))

                
        # return 0 #return value of exec_signal (success)
        return nbad_ch, outfile_list


        
if __name__=="__main__":
        ## example usage:
        ## ./run_signal.py -module 1 -t 1 -b 2 -v 1200 -d 500 -l 10
        parser = init_parser(key="signal_sipm")
        args = parser.parse_args()
        outdir = get_outdir(args)
        logger.setup(logname="Signal_sipm", logfile=unique_filename(outdir+"/signal_sipm.log"), debug_mode = args.debug)

        svn_ver, cmd = get_info()
        logger.log(logger.TEST_LEVEL_INFO, "SVN revision: "+svn_ver)
        logger.log(logger.TEST_LEVEL_INFO, "Running command: "+cmd)

        result, outfile = exec_signal_sipm(args)
        if (result == 0): logger.log(logger.TEST_LEVEL_PASS,"Finished working on signal.")
        else: logger.log(logger.TEST_LEVEL_FAIL,"Failure while working on signal.")

 
        '''
        parser = argparse.ArgumentParser()
        parser.add_argument("-m" ,"--module", help="Module ID", type=int, default=0)
        parser.add_argument("-mt" ,"--moduletag", help="tag to be appended to output folder", type=str, default="")
        parser.add_argument("-o" ,"--outname", help="output name to be prepended to the output file name", type=str, default="signal")
        parser.add_argument("-D" ,"--outdir", help="output directory path where to save data", type=str, default="./")
        parser.add_argument("-ped" ,"--pedname", help="output name to be prepended to the pedestal file to perform calibration", type=str, default="pedestal")
        parser.add_argument("-pdb" ,"--peddatabase", help="pedestal database file (including full path)", type=str, default=None)
        parser.add_argument("-s" ,"--signalscan", help="activate signal amplitude scan", action="store_true")
        parser.add_argument("-da" ,"--disable-analysis", help="flag to disable analysis", action="store_true")
        parser.add_argument("-dt" ,"--disable-datataking", help="flag to disable datataking", action="store_true")
        parser.add_argument("-c" ,"--channel0", help="channel from which the analysis starts", type=int, default=0)
        parser.add_argument("-n" ,"--nchannels", help="number of channels to be analyzed starting from channel specified with -c option", type=int, default=64)

        if testing_mode:
                parser.add_argument("-vp" ,"--vped", help="Vped to use", type=int, default=1200)
                parser.add_argument("--signalfreq", help="provide signal frequency in Hz", type=float, default=1113)
                parser.add_argument("--signalvals", help="provide start, stop and step values for signal scan in Volt", nargs="+", type=float, default=[0.2])
                parser.add_argument("-b" ,"--nblocks", help="number of Blocks of 32 samples", type=int, default=8)
                parser.add_argument("-p" ,"--packets", help="number of packets per event", type=int, default=8)
                parser.add_argument("-l" ,"--length", help="acquisition time in seconds", type=float, default=10)
                parser.add_argument("-t" ,"--triggertype", help="trigger type: 0=internal, 1=external, 2=hardsync", type=int, default=1)
                parser.add_argument("-d" ,"--triggerdelay", help="triggerdelay", type=int, default=500)
        '''
  
