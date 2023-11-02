#!/usr/bin/env python

import sys
import os
from TC_analysis_utils import *
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import yaml

testing_mode = True
## fix default daq values before turning off testing mode
defaults = {
        "nblocks": 8,
        "packets":8,
        "daq_time": 10.,
        "triggerdelay": 500,
        "triggertype": 1,
        "vped": 1200,
        "vpedstart": 100,
        "vpedstop": 4000,
        "vpedstep": 100,
        "sigstart": 0,
        "sigstop": 0.3,
        "sigstep": 0.05,
        "sigfreq": 1113,
}


if __name__=="__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-m" ,"--module", help="Module ID", type=int, default=0)
    parser.add_argument("-mt" ,"--moduletag", help="tag to be appended to output folder", type=str, default="")
    parser.add_argument("-o" ,"--outname", help="output name to be prepended to the output file name", type=str, default="pedestal")
    parser.add_argument("-D" ,"--outdir", help="output directory path where to save data", type=str, default="./")
    parser.add_argument("-v" ,"--vpedscan", help="activate vped scan", action="store_true")
    parser.add_argument("-s" ,"--signalscan", help="activate signal amplitude scan", action="store_true")
    #parser.add_argument("-da" ,"--disable-analysis", help="flag to disable analysis", action="store_true")
    #parser.add_argument("-dt" ,"--disable-datataking", help="flag to disable datataking", action="store_true")
    parser.add_argument("-c" ,"--channel0", help="channel from which the analysis starts", type=int, default=0)
    parser.add_argument("-n" ,"--nchannels", help="number of channels to be analyzed starting from channel specified with -c option", type=int, default=64)

    if testing_mode:
        parser.add_argument("-vp" ,"--vped", help="Vped to use", type=int, default=1200)
        #parser.add_argument("--vpedvals", help="provide start, stop and step values vped scan", nargs="+", type=int, default=[4000])
        parser.add_argument("--signalfreq", help="provide signal frequency in Hz", type=float, default=1113)
        parser.add_argument("--signalvals", help="provide start, stop and step values for signal scan in Volt", nargs="+", type=float, default=[0.2])
        parser.add_argument("-b" ,"--nblocks", help="number of Blocks of 32 samples", type=int, default=8)
        parser.add_argument("-p" ,"--packets", help="number of packets per event", type=int, default=8)
        #parser.add_argument("-l" ,"--length", help="acquisition time in seconds, ignored for hardsync pedestal", type=float, default=10)
        parser.add_argument("-t" ,"--triggertype", help="trigger type: 0=internal, 1=external, 2=hardsync", type=int, default=1)
        parser.add_argument("-d" ,"--triggerdelay", help="trigger delay", type=int, default=500)
        
    args = parser.parse_args()

    moduleID = int(args.module)
    vpedscan = args.vpedscan
    signalscan = args.signalscan

    disable_analysis = args.disable_analysis
    disable_datataking = args.disable_datataking
    ch0 = int(args.channel0)
    nch = int(args.nchannels)

    if testing_mode:
        nblocks = int(args.nblocks)
        packets = int(args.packets)
        #daq_time = args.length
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
        signalvals=args.signalvals
        sigfreq=args.signalfreq
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
        vpedstart = defaults["vpedstart"]
        vpedstop = defaults["vpedstop"]
        vpedstep = defaults["vpedstep"]
        sigstart = defaults["sigstart"]
        sigstop = defaults["sigstop"]
        sigstep = defaults["sigstep"]
        sigfreq = defaults["sigfreq"]

        
    outdir = args.outdir+"/"
    if testing_mode:
        outdir += "testing/"
    outdir += "Module"+str(moduleID)
    if args.moduletag!="":
        outdir += "_"+args.moduletag
    outdir += "/"
    os.system("mkdir -p "+str(outdir))
    plotdir = outdir+"summary_plots/"
    os.system("mkdir -p "+str(plotdir))
    
    if vpedscan:
        vpeds = range(vpedstart,vpedstop,vpedstep)
        outfiles = []
    
        for _vp in vpeds:
            outfile = outdir+"/"+args.outname
            if triggertype==1:
                outfile+="_exttrigger"
            elif triggertype==2:
                outfile+="_hardsync"
            #outfile+="_nblocks"+str(nblocks)+"_packets"+str(packets)+"_vped"+str(_vp)+"_delay"+str(triggerdelay)+"_r0.tio"
            outfile+="_nblocks"+str(nblocks)+"_packets"+str(packets)+"_vped"+str(_vp)+"_r0.tio"
            print("Output file:", outfile)
            outfiles.append(outfile)
        
        #vped_val = np.arange(1000,1900,200)
        #vped_val=[1000,1200]
        #filename_pedestal="testing/Module2_190907/pedestal_exttrigger_nblocks4_packets4_vped%i_delay500_r0.tio"
        #run_ped("data/"+filename_pedestal,vped_val)

        #filename_res = filename_pedestal.replace("_r0.tio","/results_pedestal.txt")
        do_pedestal_plots(outfiles,vpeds, plotdir)


    if signalscan:
        outfiles = []
        ampl_list=np.arange(sigstart,sigstop,sigstep)
        for _sigamp in ampl_list:
            tag="_signal{0:.4f}".format(_sigamp)
            outfile = outdir+"/"+args.outname
            if triggertype==1:
                outfile+="_exttrigger"
            elif triggertype==2:
                outfile+="_hardsync"
            elif triggertype==0:
                outfile+="_inttrigger"

                
            outfile += tag
                        
            outfile+="_nblocks"+str(nblocks)+"_packets"+str(packets)+"_vped"+str(vped)+"_delay"+str(triggerdelay)+"_r0.tio"
            print("Output file:", outfile)
            outfiles.append(outfile)
            
        do_signal_plots(outfiles,ampl_list, plotdir, asics=range(4))

    exit()
    #ampl_list_dict={"0.0":0,"0.05":0.05, "0.1":0.1,"0.15000000000000002":0.15,"0.2":0.2, "0.25":0.25 }
    #ampl_list_dict={"0.2":0.2,"0.4":0.4,"0.6000000000000001":0.6,"0.8":0.8}
    #ampl_list_dict={"0.2":0.2,"0.4":0.4,"0.6000000000000001":0.6,"0.8":0.8,"1.0":1.0, "1.2000000000000002":1.2, "1.4000000000000001":1.4}
    ampl_list = np.arange(0.2, 4.1, 0.2)
    idx = np.where(np.logical_or(ampl_list==2.0, ampl_list==0.4, ampl_list==4.6))[0]
    ampl_list = np.delete(ampl_list, idx)
    idx = np.where(np.logical_and(ampl_list>4.5, ampl_list<4.7))
    ampl_list = np.delete(ampl_list, idx)
    filename_signal="testing/Module2_191008/signal_pri_exttrigger_signal{0:.1f}_nblocks4_packets4_vped1200_delay450_r0.tio"
    #run_sig("data/"+filename_signal,ampl_list_dict)

    filename_res = filename_signal.replace("_r0.tio","/results_signal.txt")

    do_signal_plots(filenames,ampl_list, outdir, asics=range(4))
    #do_signal_plots(filename_res,ampl_list, asic0=0)

    
    ampl_list = np.arange(0.2, 4.1, 0.2)
    idx = np.where(np.logical_and(ampl_list>3.7, ampl_list<3.9))
    ampl_list = np.delete(ampl_list, idx)
    filename_signal="testing/Module2_191008/signal_aux_exttrigger_signal{0:.1f}_nblocks4_packets4_vped1200_delay450_r0.tio"    
    filename_res = filename_signal.replace("_r0.tio","/results_signal.txt")
    do_signal_plots(filename_res,ampl_list, asic0=2)


    fname = "testing/Module2_191008/signal_pri_exttrigger_signal4.0_nblocks4_packets4_vped1200_delay450/results_timediff_ch0_0.yaml"
    asic = 0
    do_2d_plots(fname, asic)
    fname = "testing/Module2_191008/signal_pri_exttrigger_signal4.0_nblocks4_packets4_vped1200_delay450/results_timediff_ch0_16.yaml"
    asic = 1
    do_2d_plots(fname, asic)
    fname = "testing/Module2_191008/signal_aux_exttrigger_signal4.0_nblocks4_packets4_vped1200_delay450/results_timediff_ch0_32.yaml"
    asic = 2
    do_2d_plots(fname, asic)
    fname = "testing/Module2_191008/signal_aux_exttrigger_signal4.0_nblocks4_packets4_vped1200_delay450/results_timediff_ch0_48.yaml"
    asic = 3
    do_2d_plots(fname, asic)
