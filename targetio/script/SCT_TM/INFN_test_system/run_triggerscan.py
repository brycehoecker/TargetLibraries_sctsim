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
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection


#this function looks for sections of a plot where y is within a min and max value
#useful to determine the position of plateau or peaks
def findstreak(xvals,yvals, miny, maxy):
        streakcount = 0
        best_streakcount = 0
        in_streak = False
        streak_begin = None
        streak_end = None
        best_streak_begin = None
        best_streak_end = None
        for x , y in zip(xvals, yvals):
           if y >= miny and y <= maxy:
              if in_streak:
                streakcount = streakcount+1
                streak_end = x
              else:
                in_streak = True
                streak_begin = x
                streak_end = x #important
                streakcount = 1
           else:
              if in_streak:
                in_streak = False;
                if streakcount > best_streakcount:
                  best_streakcount = streakcount
                  best_streak_begin = streak_begin
                  best_streak_end = streak_end

        if in_streak: #if still in streak on the upper end...
          logger.debug("was in streak")
          streak_end = xvals[-1]
          if streakcount > best_streakcount:
                  best_streakcount = streakcount
                  best_streak_begin = streak_begin
                  best_streak_end = streak_end


        logger.debug("best_streak_end = " + str(best_streak_end))
        return best_streakcount, best_streak_begin, best_streak_end



def choose_pmtref4(datafile, group, outdir, target_hz):
        d = yaml.load(open(datafile), Loader=yaml.Loader)
        pmtref4_vec = d["pmtref4"]
        rates = d["rates"]

        chosen_pmtref4 = 0
        for i, rate in enumerate(rates):
             if (rate > target_hz/2):
               chosen_pmtref4 = pmtref4_vec[i]
               logger.info("chosen pmtref4: " + str(chosen_pmtref4))
               break

        chosen_pmtref4_filename = outdir + "/chosen_pmtref4.yaml"
        chosen_pmtref4_dict = {}
        try:
          chosen_pmtref4_file = open(chosen_pmtref4_filename, "r")
          chosen_pmtref4_dict = yaml.load(chosen_pmtref4_file, Loader = yaml.Loader)
          if chosen_pmtref4_dict == None: chosen_pmtref4_dict = {}
          chosen_pmtref4_file.close()

        except FileNotFoundError:
          logger.log(logger.TEST_LEVEL_INFO, "creating new file " + chosen_pmtref4_filename)
          open(chosen_pmtref4_filename, "w").close() #create empty file

        chosen_pmtref4_dict[group] = chosen_pmtref4
        chosen_pmtref4_file = open(chosen_pmtref4_filename, "w")
        yaml.dump(chosen_pmtref4_dict, chosen_pmtref4_file, default_flow_style=False)
        chosen_pmtref4_file.close()


def plot_triggerscan(group, datafile, output_dir, step, outfile_table, output, target_hz):
        import yaml
        import matplotlib.pyplot as plt
        d = yaml.load(open(datafile), Loader=yaml.Loader)
        pmtref4_vec = d["pmtref4"]
        thresh_vec = d["thresh"]
        rates = d["rates"]


        title = datafile.split("/")[-1].replace(".yaml","")


        plt.clf()
        plt.ylim(1e2, 1e5)
        plt.xlim(0, 4095)
        plt.yscale("log")

        if pmtref4_vec is None and thresh_vec is None:
                logger.log(logger.TEST_LEVEL_WARNING, "WARNING: empty data file")
        elif pmtref4_vec is not None and thresh_vec is not None:
                plt.imshow(rates, origin='lower', extent=[pmtref4_vec[0], pmtref4_vec[1], thresh_vec[0], thresh_vec[1] ], cmap='jet')
                plt.colorbar()
                plt.subplots_adjust(bottom=0.1, right=0.8, top=0.9)
                plt.xlabel("PMTRef4 value")
                plt.ylabel("threshold value")
                plt.title(title)
                plt.show()
        else:
                ylabel = "rate (Hz)"
                if pmtref4_vec is None: #this is just rate vs thresh value
                        xvec = thresh_vec
                        xlabel = "thresh value"
                else: #this is just rate vs pmtref4 value
                        xvec = pmtref4_vec
                        xlabel = "PMTRef4 value"

                if True:
                        boxes = []
                        boxes_peak = []


                        best_streakcount, best_streak_begin, best_streak_end = findstreak(xvec, rates, target_hz*0.5, target_hz*1.5)
                        logger.debug("best_streakcount= " + str(best_streakcount))

                        ax = plt.gca()
                        width = best_streak_end - best_streak_begin
                        if width < step: width = step
                        boxes.append(Rectangle((best_streak_begin, 1e2), width, target_hz-1e2))
                        pc = PatchCollection(boxes, facecolor='g', alpha=0.4)
                        ax.add_collection(pc)



                        best_streakcount_peak, best_streak_begin_peak, best_streak_end_peak = findstreak(xvec, rates, target_hz*5, float("+inf"))
                        logger.debug("best_streakcount (peak)= " + str(best_streakcount_peak))
                        width = best_streak_end_peak - best_streak_begin_peak
                        padding = 10 #enlarge peak area (just to be visible on plot)
                        boxes_peak.append(Rectangle((best_streak_begin_peak - padding , 1e2), width+2*padding, target_hz*5))
                        pc2 = PatchCollection(boxes_peak, facecolor='r', alpha=0.4)
                        ax.add_collection(pc2)


                        plateau_width = best_streakcount*step
                        peak_width = best_streakcount_peak*step
                        message = "plateau width: " + str(plateau_width)
                        message2 = "peak width: " + str(peak_width)

                        plt.text(0.99, 0.99, message, fontsize=12,  horizontalalignment='right', verticalalignment='top',transform = ax.transAxes, color = 'g')
                        plt.text(0.99, 0.94, message2, fontsize=12,  horizontalalignment='right', verticalalignment='top',transform = ax.transAxes, color = 'g')



                        outfile_table.write("{0}\t{1}\t{2}\n".format(group,plateau_width,peak_width))


                plt.text(50, target_hz, 'target: ' + str(target_hz) + ' Hz', horizontalalignment='left',
                        verticalalignment='bottom', color='r', alpha=0.3)


                plt.axhline(y=target_hz, color='r', linestyle='-', alpha=0.3)
                plt.plot(xvec,rates)
                plt.title(title)
                plt.xlabel(xlabel)
                plt.ylabel(ylabel)


        outfile = output_dir + "/" + title + ".png"
        logger.info("Plotting " + outfile)

        plt.savefig(outfile, dpi=300)



def exec_triggerscan(args):

        groupsrange = args.groupsrange
        if groupsrange == None: groupsrange = list(range(0,16))

        logger.log(logger.TEST_LEVEL_INFO, "scanning from group " + str(groupsrange[0]) + " to " + str(groupsrange[-1]))

        moduleID = int(args.module)
        vpedscan = args.vpedscan
        disable_datataking = args.disable_datataking
        disable_analysis = args.disable_analysis
        nbad_ch = 0
        if testing_mode:
                wbias = int(args.wbias)
                gain = int(args.gain)
                pmtref4 = int(args.pmtref4)
                thresh = int(args.thresh)
                vped=int(args.vped)
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
                wbias = defaults["wbias"]
                gain = defaults["gain"]
                pmtref4 = defaults["pmtref4"]
                thresh = defaults["thresh"]
                vped = defaults["vped"]
                vpedstart = defaults["vpedstart"]
                vpedstop = defaults["vpedstop"]
                vpedstep = defaults["vpedstep"]

        if vpedscan:
                vpeds = range(vpedstart,vpedstop,vpedstep)
        else:
                vpeds = [vped]


        target_hz = args.signalfreq
        exttrig = args.external_trigger
        pmtref4vals=args.pmtref4vals
        if pmtref4vals is None:
                pmtref4_vec = None
        else:
                if len(pmtref4vals)>2:
                        pmtref4start = pmtref4vals[0]
                        pmtref4stop = pmtref4vals[1]
                        pmtref4step = pmtref4vals[2]
                elif len(pmtref4vals)==2:
                        pmtref4start = pmtref4vals[0]
                        pmtref4stop = pmtref4vals[1]
                        pmtref4step = 100
                elif len(pmtref4vals)==1:
                        pmtref4start = 100
                        pmtref4stop = pmtref4vals[0]
                        pmtref4step = 100
                pmtref4_vec = range(pmtref4start, pmtref4stop, pmtref4step)

        threshvals=args.threshvals
        if threshvals is None:
                thresh_vec = None
        else:
                if len(threshvals)>2:
                        threshstart = threshvals[0]
                        threshstop = threshvals[1]
                        threshstep = threshvals[2]
                elif len(threshvals)==2:
                        threshstart = threshvals[0]
                        threshstop = threshvals[1]
                        threshstep = 100
                elif len(threshvals)==1:
                        threshstart = 100
                        threshstop = threshvals[0]
                        threshstep = 100
                thresh_vec = np.arange(threshstart, threshstop, threshstep).astype(int).tolist()

        if args.enable_sipm:
                enable_HV=args.enable_hv
                disable_smart_channels=args.disable_smart_channels
                smart_dacs=args.smart_dacs
                smart_global=args.smart_global
                if type(smart_dacs) is list and len(smart_dacs)==1:
                        smart_dacs = smart_dacs[0]


        outdir = args.outdir
        if testing_mode:
                outdir += "/testing"
        outdir += "/Module"+str(moduleID)
        if args.moduletag!="":
                outdir += "_"+args.moduletag
        os.system("mkdir -p "+str(outdir))


        logger.debug("OUTDIR ---->" + outdir)

        #groups = range(groupsrange[0], groupsrange[1]+1)
        groups = groupsrange
        for _vp in vpeds:
                outfile = outdir+"/"+args.outname
                if pmtref4_vec is not None:
                        outfile += "_pmtref4"
                if thresh_vec is not None:
                        outfile += "_thresh"
                outfile += "_vped" + str(_vp)

                pmtref4_new = pmtref4 #load default (single value, not array)
                if pmtref4_vec == None: #if this is a threshold scan, load pmtref4 values as a 2d array
                  chosen_pmtref4_filename = outdir + "/chosen_pmtref4.yaml"
                  chosen_pmtref4_dict = {}
                  try:
                    chosen_pmtref4_file = open(chosen_pmtref4_filename, "r")
                    chosen_pmtref4_dict = yaml.load(chosen_pmtref4_file, Loader = yaml.Loader)
                    if chosen_pmtref4_dict != None:
                      pmtref4_new = [[pmtref4 for i in range(4)] for j in range(4)]
                    for g in range(16):
                        if g in chosen_pmtref4_dict:
                          pmtref4_new[g//4][g%4] = chosen_pmtref4_dict[g]
                        else:
                          pmtref4_new[g//4][g%4] = pmtref4 #set the default value
                        logger.info("Loaded from file " + chosen_pmtref4_filename + ": pmtref4 of group " + str(g) + " is " + str(pmtref4_new[g//4][g%4]))
                    chosen_pmtref4_file.close()

                  except FileNotFoundError:
                    logger.log(logger.TEST_LEVEL_FAIL, "chosen_pmtref4 file not found " + chosen_pmtref4_filename)
                    return 1


                if not args.disable_datataking:
                        logger.info("PMTREF4: " + str(pmtref4_new))
                        if not args.enable_sipm:
                                do_triggerscan(outfile, groups=groups, trigger_duration = 0.1, 
                                              pmtref4_vec=pmtref4_vec, thresh_vec=thresh_vec, 
                                              vped=vped, wbias=wbias, pmtref4=pmtref4_new, 
                                              thresh=thresh, gain=gain, exttrig=exttrig)#, target_hz=args.signalfreq)
                        else:
                                do_triggerscan_sipm(outfile, groups=groups, trigger_duration = 0.1,
                                                    pmtref4_vec=pmtref4_vec, thresh_vec=thresh_vec,
                                                    vped=vped, wbias=wbias, pmtref4=pmtref4_new,
                                                    thresh=thresh, gain=gain, exttrig=exttrig,
                                                    enable_HV=enable_HV, disable_smart_channels=disable_smart_channels,
                                                    smart_dacs=smart_dacs, smart_global=smart_global)

                        if thresh_vec is None and pmtref4_vec is not None: #if this is a pmtref4 scan
                          logger.info ("Choosing pmtref4 values...")
                          for g in groups:
                              datafile = outfile + "_group" + str(g) + ".yaml"
                              choose_pmtref4(datafile, g, outdir, target_hz)
                          logger.info("Done.")






                outfiles = [outfile + "_group" + str(group) + ".yaml" for group in groups]
                ## analysis part starts here
                analysis_dir = outfile + "/"
                os.system("mkdir -p " + str(analysis_dir))
                #print("outfiles = {}".format(outfiles))
                nbad_ch = analyse_triggerscan(outfiles, outdir=analysis_dir, 
                                    limitsdir = "./", fname_limits="limits.yaml",
                                    target_hz = target_hz,g0=groupsrange[0],
                                    ng=len(groupsrange),
                                    tag="")
        ## summary vs Vped
        if len(vpeds) > 1:
                # read results : average_ped vs vped, noise (avg, per chan) vs vped
                # do plots/fit

                pass

        return nbad_ch

if __name__=="__main__":
        ## example usage:
        ## ./run_triggerscan.py -m 1 --pmtref4vals 1800 2200 2 --threshvals 1500 2200 10
        parser = init_parser(key="trigger")
        args = parser.parse_args()
        outdir = get_outdir(args)
        logger.setup(logname="Trigger", logfile=unique_filename(outdir+"/trigger.log"), debug_mode = args.debug)

        svn_ver, cmd = get_info()
        logger.log(logger.TEST_LEVEL_INFO, "SVN revision: "+svn_ver)
        logger.log(logger.TEST_LEVEL_INFO, "Running command: "+cmd)

        result = exec_triggerscan(args)
        if (result == 0): logger.log(logger.TEST_LEVEL_PASS,"Finished working on trigger.")
        else: logger.log(logger.TEST_LEVEL_FAIL,"Failure while working on trigger.")

