#!/usr/bin/env python
import argparse
from agilent33250A_off import agilent33250A_off
from agilent33250A_inverted import agilent33250A_inverted
from run_pedestal import *
from run_signal import *
from run_signal_sipm import *
from run_triggerscan import *
from run_power import *
from run_peltier import *
from run_smart import *
from utils import *
from MyLogging import logger
from sys import platform


# default tag
# pulse amplitude as commanded to the function generator, for the first signal run

parser = argparse.ArgumentParser()
parser.add_argument("module_number",
                    help="serial number of the module being tested")
parser.add_argument("-cfg", "--config",
                    help="config file name", type=str, default="defaults_smart.yaml")
parser.add_argument("-p", "--pedestal",
                    help="flag to enable pedestal data taking", action="store_true")
parser.add_argument("-dc", "--checkpoint",
                    help="flag to disable checkpoint after pedestal", action="store_false")
parser.add_argument("-s", "--signal",
                    help="flag to enable signal data taking", action="store_true")
parser.add_argument("-l", "--linearity",
                    help="flag to enable linearity test", action="store_true")
parser.add_argument("-g", "--triggerscan",
                    help="flag to enable triggerscan", action="store_true")
parser.add_argument("-w", "--power",
                    help="flag to enable power and bias voltage levels", action="store_true")
parser.add_argument("-u", "--peltier", ##uC
                    help="flag to enable peltier and thermistors tests", action="store_true")
parser.add_argument("-a", "--smart", ##smart
                    help="flag to enable smart ADC tests", action="store_true")
parser.add_argument("-uf", "--peltier-firmware", ##uC
                    help="flag to enable peltier firmware writing", action="store_true")
parser.add_argument("-v", "--vpedscan",
                    help="flag to enable vped scan", action="store_true")
parser.add_argument("-da", "--disable-analysis",
                    help="flag to disable analysis", action="store_true")
parser.add_argument("-dt", "--disable-datataking",
                    help="flag to disable datataking", action="store_true")
parser.add_argument("-ds", "--disable-summary",
                    help="flag to disable summary", action="store_true")
parser.add_argument("-t", "--tag",
                    help="tag to be appended to output folder", type=str, default="")
parser.add_argument("-c", "--channel0",
                    help="channel from which the analysis starts", type=int, default=0)
parser.add_argument("-n", "--nchannels",
                    help="number of channels to analyse", type=int, default=64)
parser.add_argument("-g0", "--group0",
                    help="trigger groups from which the analysis starts", type=int, default=0)
parser.add_argument("-ng", "--ngroups",
                    help="number of trigger groups to analyse", type=int, default=16)
parser.add_argument("-dbg", "--debug",
                    help="flag to enable debug messages on console", action="store_true")
parser.add_argument("-stu", "--showtable_peltier",
                    help="flag to show a summary table after peltier run", action="store_true")
parser.add_argument("-stw", "--showtable_power",
                    help="flag to show a summary table after power run", action="store_true")
parser.add_argument("-sta", "--showtable_smart",
                    help="flag to show a summary table after smart run", action="store_true")
parser.add_argument("-stp", "--showtable_pedestal",
                    help="flag to show a summary table after pedestal run", action="store_true")
parser.add_argument("-sts", "--showtable_signal",
                    help="flag to show a summary table after signal run", action="store_true")
parser.add_argument("-stl", "--showtable_linearity",
                    help="flag to show a summary table after linearity run", action="store_true")
parser.add_argument("-stv", "--showtable_vped",
                    help="flag to show a summary table after vped run", action="store_true")
parser.add_argument("-stg", "--showtable_triggerscan",
                    help="flag to show a summary table after trigger run", action="store_true")
parser.add_argument("-npg", "--no-pulse-generator",
                    help="flag to force the DAQ for pedestal and vpedscan tests, \
                    when the pulse generator is not available.", action="store_false")

#parser.add_argument("-packets", "--packets",
#                    help="number of packets used in network stream", type=int, default=8)
# parser.add_argument("-vp","--default_vped", help="default pedestal voltage (vped) to be used", type=int, default=1200)
# parser.add_argument("-pf","--pulse_frequency", help="frequency to use for the pulse generator in Hertz", type=int, default=1113)
args = parser.parse_args()

# note: to recreate summary plots only (useful when debugging), put both -da and -dt options

# Read config file and store in the dval dictionary
with open(args.config, 'r') as ymlfile:
    dval = yaml.safe_load(ymlfile)

if "run"==args.tag and args.pedestal:
    fname="last_run.dat"
    try:
        with open(fname,"r+") as rfile:
            rn=int(rfile.readlines()[-1])+1
            rfile.write(str(rn)+"\n")
    except:
        with open(fname,"w") as rfile:
            rn=0
            rfile.write(str(rn)+"\n")
    args.tag+=str(rn)
    rfile.close()
elif "run"==args.tag and not (args.pedestal):
    fname="last_run.dat"
    with open(fname,"r+") as rfile:
        rn=int(rfile.readlines()[-1])
    args.tag+=str(rn)
    rfile.close()
    
TAG = args.tag
ENABLE_POWER_AND_SIGNAL_INTEGRITY_TEST = args.power
ENABLE_PELTIER = args.peltier
ENABLE_SMART_ADC = args.smart
ENABLE_PEDESTAL = args.pedestal
ENABLE_SIGNAL = args.signal
ENABLE_LINEARITY = args.linearity
ENABLE_VPED_SCAN = args.vpedscan
ENABLE_TRIGGER_SCAN = args.triggerscan
CHECKPOINT_AFTER_PEDESTAL = args.checkpoint
CHECKPOINT_AFTER_SIGNAL = dval['signal']['checkpoint_enabled']
CHECKPOINT_AFTER_LINEARITY = dval['linearity']['checkpoint_enabled']
CHECKPOINT_AFTER_VPEDSCAN = dval['vpedscan']['checkpoint_enabled']
CHECKPOINT_AFTER_TRIGSCAN_PMTREF4 = dval['trigscan_pmtref4']['checkpoint_enabled']
CHECKPOINT_AFTER_TRIGSCAN_THR = dval['trigscan_thr']['checkpoint_enabled']

CHANNEL0 = args.channel0
NCHANNELS = args.nchannels  # set to 1 to speed up during debug
PULSE_GENERATOR = args.no_pulse_generator
OUTDIR = dval['global']['outdir']
# DAQ parameters
#packets = args.packets
PACKETS = dval['daq']['packets']
NBLOCKS = dval['daq']['nblocks']


# Pulse amplitude for signal run:
PULSE_AMPLITUDE_VOLTS = dval['signal']['pulse_amp']
# Pulse amplitude used for trigger rate scan over PMTRef4 parameter
PULSE_AMPLITUDE_VOLTS_TRIGGERSCAN_PMTREF4 = dval['trigscan_pmtref4']['pulse_amp_t_PMTREF4']
# Pulse amplitude used for trigger rate scan over "thresh" parameter
PULSE_AMPLITUDE_VOLTS_TRIGGERSCAN_THRESH = dval['trigscan_thr']['pulse_amp_t_THRESH']
# Allows up to 10 V amplitude (-5 V to +5V)
PULSE_OFFSET = dval['global']['pulse_offset']
# Stepsize for triggerscan over "PMTRef4" parameter
TRIGGERSCAN_PMTREF4_STEPSIZE = dval['daq']['trig_PMTREF4_stepsize']
# Stepsize for trigger rate scan over "thresh" parameter
TRIGGERSCAN_THRESH_STEPSIZE = dval['daq']['trig_THRESH_stepsize']
# Trigger delay in ns
TRIGGERDELAY = dval['daq']['trig_del']
# Range of groups to test with trigger rate scan
#GROUPSRANGE = [0, args.ngroups-1]
GROUPSRANGE = list(range(args.group0,args.group0+args.ngroups))

# Default vped
DEF_VPED = dval['pedestal']['default_vped']
# Pulse frequency
PULSE_FREQ = dval['global']['pulse_freq']

MIN_BADCHANNELS_THRESHOLD_FOR_CHECKPOINT_PEDESTAL = dval['pedestal']['min_badchannels_threshold_for_checkpoint']
MIN_BADCHANNELS_THRESHOLD_FOR_CHECKPOINT_SIGNAL = dval['signal']['min_badchannels_threshold_for_checkpoint']
MIN_BADCHANNELS_THRESHOLD_FOR_CHECKPOINT_LINEARITY = dval['linearity']['min_badchannels_threshold_for_checkpoint']
MIN_BADCHANNELS_THRESHOLD_FOR_CHECKPOINT_VPEDSCAN = dval['vpedscan']['min_badchannels_threshold_for_checkpoint']
MIN_BADCHANNELS_THRESHOLD_FOR_CHECKPOINT_TRIGSCAN_PMTREF4 = dval['trigscan_pmtref4']['min_badchannels_threshold_for_checkpoint']
MIN_BADCHANNELS_THRESHOLD_FOR_CHECKPOINT_TRIGSCAN_THR = dval['trigscan_thr']['min_badchannels_threshold_for_checkpoint']
MIN_BADCHANNELS_THRESHOLD_FOR_CHECKPOINT_SMART_CALIB = dval['smart_calib']['min_badchannels_threshold_for_checkpoint']

# logger.stdout_handler.setLevel(args.terminal_debug_level)
# logger.file_handler.setLevel(args.file_debug_level)


def yes_or_no(question):
    answer = input(question + " (yes/no): ").lower().strip()
    print("")
    while not(answer == "y" or answer == "yes" or
              answer == "n" or answer == "no"):
        print("Input yes or no")
        answer = input(question + "(y/n):").lower().strip()
        print("")
    if answer[0] == "y":
        return True
    else:
        return False


# compute output directory name
#if (args.tag is not None) and (args.tag != ""):
#    outdir = "testing/Module" + str(args.module_number) + str("_") + args.tag
#else:
#    outdir = "testing/Module"+str(args.module_number)
outdir = get_outdir1(args.module_number, OUTDIR, args.tag)

if not os.path.exists(outdir):
    os.makedirs(outdir)

check_status_files(outdir=outdir, smart_flag=True)

logger.setup(logname="main", logfile=unique_filename(
    outdir+"/main.log"), debug_mode=args.debug)
svn_ver, cmd = get_info()

update_global_connection_details(my_ip=dval["global"].get("my_ip"),module_ip=dval["global"].get("module_ip"),
                                 asic_def=dval["global"].get("tc_def"),trigger_asic_def=dval["global"].get("t5tea_def"),
                                 module_def=dval["global"].get("fpga_def"))

# show chosen options
logger.log(logger.TEST_LEVEL_INFO, "SVN revision: "+svn_ver)
logger.log(logger.TEST_LEVEL_INFO, "Running command: "+cmd)
logger.log(logger.TEST_LEVEL_INFO, "TC def file: "+dval["global"].get("tc_def"))
logger.log(logger.TEST_LEVEL_INFO, "T5TEA def file: "+dval["global"].get("t5tea_def"))
logger.log(logger.TEST_LEVEL_INFO, "FPGA def file: "+dval["global"].get("fpga_def"))
logger.log(logger.TEST_LEVEL_INFO, "Chosen options: ")
logger.log(logger.TEST_LEVEL_INFO, "TAG: \"" + args.tag + "\"")
logger.log(logger.TEST_LEVEL_INFO,
           "Pulse amplitude for signal run: " +
           str(PULSE_AMPLITUDE_VOLTS) + " V")
logger.log(logger.TEST_LEVEL_INFO,
           "Pulse amplitude for trigger rate scan over PMTRef4: " +
           str(PULSE_AMPLITUDE_VOLTS_TRIGGERSCAN_PMTREF4) + " V")
logger.log(logger.TEST_LEVEL_INFO,
           "Pulse amplitude used for trigger rate scan over \"thresh\" parameter: " +
           str(PULSE_AMPLITUDE_VOLTS_TRIGGERSCAN_THRESH) + " V")
logger.log(logger.TEST_LEVEL_INFO,
           "Commanded pulse frequency to the function generator (Hz): " + str(PULSE_FREQ))
logger.log(logger.TEST_LEVEL_INFO, "Pulse offset: " + str(PULSE_OFFSET) + " V")
#logger.log(logger.TEST_LEVEL_INFO, "Note: pulse offset 0 enables 10 V pulses (-5 V to 5 V), also note that the output of the fanout board is AC coupled")
logger.log(logger.TEST_LEVEL_INFO,
           "Default Vped: " + str(DEF_VPED) + " DAC units")
logger.log(logger.TEST_LEVEL_INFO,
           "Stepsize for triggerscan over \"PMTRef4\" parameter: " +
           str(TRIGGERSCAN_PMTREF4_STEPSIZE) + " DAC units")
logger.log(logger.TEST_LEVEL_INFO,
           "Stepsize for trigger rate scan over \"thresh\" parameter: " +
           str(TRIGGERSCAN_THRESH_STEPSIZE) + " DAC units")
logger.log(logger.TEST_LEVEL_INFO, "Trigger delay: " +
           str(TRIGGERDELAY) + " ns")
logger.log(logger.TEST_LEVEL_INFO,
           "Starting channel for the analysis (channel 0 is default): " +
           str(CHANNEL0))
logger.log(logger.TEST_LEVEL_INFO,
           "Number of channels to analyse (64 for all channels, set to 1 to speed up for debugging purposes): " +
           str(NCHANNELS))
logger.log(logger.TEST_LEVEL_INFO,
           "Range of trigger groups to test (index: 0 to 15): " +
           str(GROUPSRANGE))
logger.log(logger.TEST_LEVEL_INFO, "Enable power and signal integrity test: " +
           str(ENABLE_POWER_AND_SIGNAL_INTEGRITY_TEST))
logger.log(logger.TEST_LEVEL_INFO,
           "Enable pedestal data taking: " + str(ENABLE_PEDESTAL))
logger.log(logger.TEST_LEVEL_INFO,
           "Enable signal data taking/analysis: " + str(ENABLE_SIGNAL))
logger.log(logger.TEST_LEVEL_INFO,
           "Enable linearity data taking/analysis: " + str(ENABLE_LINEARITY))
logger.log(logger.TEST_LEVEL_INFO, "Enable trigger scan: " +
           str(ENABLE_TRIGGER_SCAN))


#os.system('echo This is C stdout')  # testing redirection of stdout for logging
#os.system('echo This is C stderr >&2')  # testing stderr redirection for logging



def checkpoint(checkpoint_name, checkpoint_question_enabled, badchannels, badchannels_threshold):
    test_status = False
    if (badchannels>0):
        logger.log(logger.TEST_LEVEL_FAIL, str(badchannels) + " channels did not pass the test. " + checkpoint_name + " test: FAIL.")
    else:
        logger.log(logger.TEST_LEVEL_PASS, checkpoint_name+ " test: SUCCESS.")
        test_status = True

    if badchannels > badchannels_threshold:
        logger.log(logger.TEST_LEVEL_FAIL, "The number of bad channels is above the threshold limit for " + checkpoint_name.lower() + " test. You may want to abort the test at this point.")


    if checkpoint_question_enabled and badchannels > badchannels_threshold:
        logger.log(logger.TEST_LEVEL_INFO,
                    "Opening " + checkpoint_name.lower() + " summary results: ")
        print("Please check the " +  checkpoint_name.lower() + " analysis output. Type \"yes\" or \"y\" to carry on with the other tests, or \"no\" to abort now")

        if yes_or_no("Continue?"):
                pass

        else:
            logger.log(logger.TEST_LEVEL_INFO,
                        "Aborted by user choice after " + checkpoint_name.lower() + ".")
            exit(1)

    return test_status



if (ENABLE_POWER_AND_SIGNAL_INTEGRITY_TEST):
    logger.log(logger.TEST_LEVEL_INFO, "Starting power and signal integrity test")
    test_name, test_status = "power", False

    # args_power = argparse.Namespace(module=args.module_number,outdir=OUTDIR,moduletag=args.tag)
    args_power = argparse.Namespace(
        disable_datataking=args.disable_datataking,
        module=args.module_number,
        outdir=OUTDIR,
        moduletag=args.tag
    )

    ret = -1
    logger.log(logger.TEST_LEVEL_INFO, "Executing power and signal integrity test...")
    try:
        ret, dstatus = exec_power(args_power)
    except:
        logger.exception(
            "Could not complete power and signal integrity test, an exception occurred (check log).")
        logger.log(logger.TEST_LEVEL_FAIL,
                   "Could not complete power and signal integrity test, an exception occurred (check log).")
        exit(1)

    if ret >= 0:
          results_power_png = outdir + "/power_summary_plots/PowerAnalysis.png"
          results_power_html = outdir + "/power_summary_plots/results_clk.html"
          results_power_html2 = outdir + "/power_summary_plots/results_power.html"

          if (args.showtable_power):
            if (platform == "darwin"):
                os.system("open -a firefox {0} &".format(results_power_html))  # MAC
                os.system("open -a firefox {0} &".format(results_power_html2))  # MAC
            if (platform == "linux" or platform == "linux2"):
                os.system("firefox {0} &".format(results_power_html))
                os.system("firefox {0} &".format(results_power_html2))
          if (platform == "darwin"):
            os.system("open {0} &".format(results_power_png))  # MAC
          if (platform == "linux" or platform == "linux2"):
            os.system("eog {0} &".format(results_power_png))

          if ret == 0:
            logger.log(logger.TEST_LEVEL_PASS, "Power and signal integrity test: SUCCESS.")
            test_status = True
          else: #TODO: pass and print number of tests that failed, using checkpoint function
            logger.log(logger.TEST_LEVEL_FAIL, "Power and signal integrity test: FAILED.")

    else: #ret<0, sotware or hardware problem
          logger.log(logger.TEST_LEVEL_FAIL, "Power and signal integrity test: FAILED.")
          exit(1) #TODO: decide when to actually abort

    t_, ts_ = 'power', dstatus['power']
    update_status_files(outdir=outdir, test=t_, test_status=ts_)

    t_, ts_ = 'power_dig', dstatus['power_dig']
    update_status_files(outdir=outdir, test=t_, test_status=ts_)

    t_, ts_ = 'temp', dstatus['temp']
    update_status_files(outdir=outdir, test=t_, test_status=ts_)

    t_, ts_ = 'hv', dstatus['hv']
    update_status_files(outdir=outdir, test=t_, test_status=ts_)

    t_, ts_ = 'clk', dstatus['clk']
    update_status_files(outdir=outdir, test=t_, test_status=ts_)

    t_ = 'power_all'
    ts_ = all([dstatus['power'], dstatus['temp'], dstatus['hv']])
    update_status_files(outdir=outdir, test=t_, test_status=ts_)
    set_status_hmtl_directory(
        outdir=outdir,
        key="__POWER_SUBDIR__",
        subdir="power_summary_plots",
    )


if (ENABLE_PELTIER):
    logger.log(logger.TEST_LEVEL_INFO, "Starting Peltier and thermistors test")
    test_name, test_status = "peltier", False

    if args.peltier_firmware:
        logger.log(logger.TEST_LEVEL_INFO, "Writing Peltier uC firmware... Please wait...")
        ret = os.system("./program_controller.sh")
    else:
        logger.log(logger.TEST_LEVEL_INFO, "Initializing Peltier uC communication...")
        ret = os.system("fpgacmd -w 0x21 0x80002001")

    if (ret != 0):
        logger.log(logger.TEST_LEVEL_FAIL, "Peltier uC: could not initialize communication or could not program firmware: FAILED.")
        exit(1) #TODO: decide when to actually abort 
    else:
        args_peltier = argparse.Namespace(
            disable_datataking=args.disable_datataking,
            module=args.module_number,
            outdir=OUTDIR,
            moduletag=args.tag
        )

        ret = -1
        logger.log(logger.TEST_LEVEL_INFO, "Executing peltier and thermistors test...")
        try:
            ret = exec_peltier(args_peltier)
        except:
            logger.exception(
                "Could not complete peltier and thermistors test, an exception occurred (check log).")
            logger.log(logger.TEST_LEVEL_FAIL,
                       "Could not complete peltier and thermistors test, an exception occurred (check log).")
            exit(1)


        if ret >= 0:
          results_peltier_png = outdir + "/peltier_summary_plots/Peltier.png"
          results_peltier_html = outdir + "/peltier_summary_plots/results_peltier.html"

          if (args.showtable_peltier):
            if (platform == "darwin"):
                os.system(
                    "open -a firefox {0} &".format(results_peltier_html))  # MAC
            if (platform == "linux" or platform == "linux2"):
                os.system("firefox {0} &".format(results_peltier_html))
          if (platform == "darwin"):
            os.system("open {0} &".format(results_peltier_png))  # MAC
          if (platform == "linux" or platform == "linux2"):
            os.system("eog {0} &".format(results_peltier_png))

          if ret == 0:
            logger.log(logger.TEST_LEVEL_PASS, "Peltier and thermistors test: SUCCESS.")
            test_status = True
          else:  # TODO: pass and print number of tests that failed, using checkpoint function
            logger.log(logger.TEST_LEVEL_FAIL, "Peltier and thermistors test: FAILED.")

        else: #ret<0, sotware or hardware problem
          logger.log(logger.TEST_LEVEL_FAIL, "Peltier and thermistors test: FAILED.")
          exit(1) #TODO: decide when to actually abort
    
    update_status_files(outdir=outdir, test=test_name, test_status=test_status)
    set_status_hmtl_directory(
        outdir=outdir,
        key="__PELTIER_SUBDIR__",
        subdir="peltier_summary_plots",
    )


if (ENABLE_SMART_ADC):
    logger.log(logger.TEST_LEVEL_INFO, "Starting SMART ADC test")
    test_name, test_status = "smart", False

    args_smart = argparse.Namespace(
        disable_analysis=args.disable_analysis,
        disable_datataking=args.disable_datataking,
        module=args.module_number,
        moduletag=args.tag,
        outdir=OUTDIR,
        outname=dval['smart_calib']['outname'],
        smart_dacs=dval['smart_calib']['dacs'],
        smart_global=dval['smart_calib']['globals']
    )

    ret = -1
    logger.log(logger.TEST_LEVEL_INFO, "Executing SMART ADC test...")
    try:
        ret = exec_smart_calib(args_smart)
    except:
        logger.exception(
            "Could not complete SMART ADC test, an exception occurred (check log).")
        logger.log(logger.TEST_LEVEL_FAIL,
                   "Could not complete SMART ADC test, an exception occurred (check log).")
        exit(1)


    if ret >= 0:
        results_smart_png = outdir + "/smart_summary_plots/SmartCalib_*.png"
        results_smart_html = outdir + "/smart_summary_plots/results_smart.html"

        if (args.showtable_smart):
            if (platform == "darwin"):
                os.system("open -a firefox {0} &".format(results_smart_html))  # MAC
            if (platform == "linux" or platform == "linux2"):
                os.system("firefox {0} &".format(results_smart_html))
        if (platform == "darwin"):
            os.system("open {0} &".format(results_smart_png))  # MAC
        if (platform == "linux" or platform == "linux2"):
            os.system("eog {0} &".format(results_smart_png))

        test_status = checkpoint(
            checkpoint_name="SMART ADC", checkpoint_question_enabled=False, #CHECKPOINT_AFTER_SMART_CALIB,
            badchannels=ret, badchannels_threshold=MIN_BADCHANNELS_THRESHOLD_FOR_CHECKPOINT_SMART_CALIB
        )
        #if ret == 0:
        #    logger.log(logger.TEST_LEVEL_PASS, "SMART ADC test: SUCCESS.")
        #    test_status = True
        #else:  # TODO: pass and print number of tests that failed, using checkpoint function
        #    logger.log(logger.TEST_LEVEL_FAIL, "SMART ADC test: FAILED.")

    else: #ret<0, sotware or hardware problem
        logger.log(logger.TEST_LEVEL_FAIL, "SMART ADC test: FAILED.")
        exit(1) #TODO: decide when to actually abort
    
    update_status_files(outdir=outdir, test=test_name, test_status=test_status)
    set_status_hmtl_directory(
        outdir=outdir,
        key="__SMART_SUBDIR__",
        subdir="smart_summary_plots"
    )

    
if (ENABLE_PEDESTAL):
    test_name, test_status = "pedestal", False
    if not args.disable_datataking and PULSE_GENERATOR:
        ret = -1
        logger.log(logger.TEST_LEVEL_INFO,
                   "Turning off the function generator")
        try:
            ret = agilent33250A_inverted(
                PULSE_AMPLITUDE_VOLTS_TRIGGERSCAN_PMTREF4, PULSE_FREQ, PULSE_OFFSET, sync=True) #this is to turn on the SYNC output on the function generator
        except:
            logger.exception(
                "Could not turn off the function generator output, exception occurred. Check if function generator is on and connection.")
            logger.log(logger.TEST_LEVEL_FAIL,
                       "Could not turn off the function generator output, exception occurred. Check if function generator is on and connection.")
            exit(1)

        try:
            ret = agilent33250A_off()
        except:
            logger.exception(
                "Could not turn off the function generator output, exception occurred. Check if function generator is on and connection.")
            logger.log(logger.TEST_LEVEL_FAIL,
                       "Could not turn off the function generator output, exception occurred. Check if function generator is on and connection.")
            exit(1)

        if (ret == 0):
            logger.log(logger.TEST_LEVEL_INFO,
                       "Turn off the function generator: SUCCESS.")
        else:
            logger.log(logger.TEST_LEVEL_FAIL,
                       "Could not turn off the function generator output.")
            exit(1)

    args_pedestal = argparse.Namespace(
        channel0=CHANNEL0,
        disable_analysis=args.disable_analysis,
        disable_datataking=args.disable_datataking,
        length=dval['pedestal']['length'],
        module=args.module_number,
        moduletag=args.tag,
        nblocks=NBLOCKS, #dval['pedestal']['nblocks'],
        nchannels=NCHANNELS,
        #outdir=dval['pedestal']['outdir'],
        outdir=OUTDIR,
        outname=dval['pedestal']['outname'],
        packets=PACKETS, #args.packets,
        triggerdelay=TRIGGERDELAY,
        triggertype=dval['pedestal']['triggertype'],
        vped=DEF_VPED,
        fast_mode=dval['pedestal']['fast_mode'], 
        vpedscan=False,
        vpedvals=[4000],#dval['pedestal']['vpedvals'],
        force=False
    )

    ret = -1
    logger.log(logger.TEST_LEVEL_INFO, "Executing pedestal run...")
    try:
        ret = exec_pedestal(args_pedestal)
    except:
        logger.exception(
            "Could not complete pedestal run, an exception occurred (check log).")
        logger.log(logger.TEST_LEVEL_FAIL,
                   "Could not complete pedestal run, an exception occurred (check log).")
        exit(1)

    #pedestal_summary_path_pdf = outdir + "/pedestal_hardsync_nblocks8_packets"+str(packets)+"_vped"+str(DEF_VPED)+"/results_pedestal_plots.pdf"
    #logger.log(logger.TEST_LEVEL_INFO, "Opening pedestal summary results: " + pedestal_summary_path_pdf)
    #os.system("evince " + pedestal_summary_path_pdf)
    ped_trigtype_number = dval["pedestal"]["triggertype"]

    if (ped_trigtype_number == 2):
       ped_trigtype = "hardsync"
    else:
       ped_trigtype = "exttrig"

    sigma_distribution_summary_path_png = outdir + \
        "/pedestal_" + str(ped_trigtype) + "_nblocks" + str(NBLOCKS)+ \
        "_packets" + str(PACKETS)+"_vped"+str(DEF_VPED) + \
        "/8_summary_sigma_distribution.png"
    sigma_summary_path_png = outdir + "/pedestal_" + ped_trigtype + "_nblocks"+ str(NBLOCKS)+\
                             "_packets"+str(PACKETS)+"_vped"+str(DEF_VPED)+ \
                             "/9_summary_sigma.png"
    outliers_path_png = outdir + "/pedestal_" + ped_trigtype + "_nblocks"+str(NBLOCKS)+ \
                        "_packets"+str(PACKETS)+"_vped"+str(DEF_VPED)+ \
                        "/10_outliers.png"
    results_pedestal_html = outdir + "/pedestal_" + ped_trigtype + "_nblocks"+str(NBLOCKS)+ \
                            "_packets"+str(PACKETS)+"_vped"+str(DEF_VPED) + \
                            "/results_pedestal.html"
    results_pedestal_txt = outdir + "/pedestal_" + ped_trigtype + "_nblocks"+str(NBLOCKS)+ \
                           "_packets" + str(PACKETS)+"_vped"+str(DEF_VPED)+ \
                           "/results_pedestal.txt"
    results_pedestal_png = outdir + "/pedestal_" + ped_trigtype + "_nblocks"+str(NBLOCKS)+ \
                           "_packets" + str(PACKETS)+"_vped"+str(DEF_VPED) + \
                           "/11_results_pedestal_plots.png"

    if (ret >= 0):
        if (args.showtable_pedestal):
            if (platform == "darwin"):
                os.system(
                    "open -a firefox {0} &".format(results_pedestal_html))  # MAC
            if (platform == "linux" or platform == "linux2"):
                os.system("firefox {0} &".format(results_pedestal_html))
        if (platform == "darwin"):
            os.system("open {0} &".format(results_pedestal_png))  # MAC
        if (platform == "linux" or platform == "linux2"):
            os.system("eog {0} &".format(results_pedestal_png))

        test_status = checkpoint(
            checkpoint_name="Pedestal", checkpoint_question_enabled=CHECKPOINT_AFTER_PEDESTAL,
            badchannels=ret, badchannels_threshold=MIN_BADCHANNELS_THRESHOLD_FOR_CHECKPOINT_PEDESTAL
        )

    else:
        logger.log(logger.TEST_LEVEL_FAIL, "Pedestal test: FAIL.")

    update_status_files(outdir=outdir, test=test_name, test_status=test_status)
    set_status_hmtl_directory(
        outdir=outdir,
        key="__PEDESTAL_SUBDIR__",
        subdir="pedestal_" + ped_trigtype + "_nblocks"+str(NBLOCKS)+ \
                "_packets" + str(PACKETS)+"_vped"+str(DEF_VPED),
    )


if (ENABLE_SIGNAL):
    test_name, test_status = "signal", False

    if not args.disable_datataking:
        ret = -1
        logger.log(logger.TEST_LEVEL_INFO,
                   "Setting up function generator for pulse injection...")
        try:
            #ret = agilent33250A_inverted(
            #    PULSE_AMPLITUDE_VOLTS, PULSE_FREQ, PULSE_OFFSET)
            ret=0
        except:
            logger.exception(
                "Could not set up the function generator for pulse injection, an exception occurred (check log).")
            logger.log(logger.TEST_LEVEL_FAIL,
                       "Could not set up the function generator for pulse injection, an exception occurred (check log).")
            exit(1)

        if (ret == 0):
            logger.log(logger.TEST_LEVEL_PASS,
                       "Set up pulse injection: SUCCESS.")
        else:
            logger.log(logger.TEST_LEVEL_FAIL,
                       "Set up pulse injection: FAILED.")
            exit(1)


    args_signal = argparse.Namespace(
        channel0=CHANNEL0,
        disable_analysis=args.disable_analysis,
        disable_datataking=args.disable_datataking,
        length=dval['signal']['length'],
        module=args.module_number,
        moduletag=args.tag,
        nblocks=NBLOCKS, #dval['signal']['nblocks'],
        nchannels=NCHANNELS,
        outdir=OUTDIR, #dval['signal']['outdir'],
        outname=dval['signal']['outname'],
        packets=PACKETS, #args.packets,
        peddatabase=None,
        pedname=dval['signal']['pedname'],
        pedtrigtype=dval['pedestal']['triggertype'],
        signalfreq=PULSE_FREQ,
        signalscan=False,
        #signalvals=[0.2],#dval['signal']['signalvals'],
        triggerdelay=TRIGGERDELAY,
        triggertype=dval['signal']['triggertype'],
        pmtref4=dval['signal']['pmtref4'],
        thresh=dval['signal']['thresh'],
        vped=DEF_VPED,
        force=False,
        enable_hv=dval['signal']['hv_enable'],
        disable_smart_channels=dval['smart']['disable_channels'],
        smart_dacs=dval['smart']['dacs'],
        smart_global=dval['smart']['globals'],
        smart_flag_dacs=False,
        smart_flag_globals=False
    )

    ret = -1
    logger.log(logger.TEST_LEVEL_INFO, "Executing signal run...")
    try:
        ret, outfile_list = exec_signal_sipm(args_signal)
    except:
        logger.exception(
            "Could not complete signal run, an exception occurred (check log).")
        logger.log(logger.TEST_LEVEL_FAIL,
                   "Could not complete signal run, an exception occurred (check log).")
        exit(1)


    if ret>=0 and not args.disable_analysis:
        #results_signal_txt = outdir + "/"+dval['signal']['outname']+"_exttrigger_nblocks"+str(NBLOCKS)+ \
        #                     "_packets" + str(PACKETS)+"_vped"+str(DEF_VPED) + \
        #                     "_delay450/results_signal.txt"
        #results_signal_html = outdir + "/"+dval['signal']['outname']+"_exttrigger_nblocks"+str(NBLOCKS)+ \
        #                      "_packets" + str(PACKETS)+"_vped"+str(DEF_VPED) + \
        #                      "_delay450/results_signal.html"
        #results_signal_png = outdir + "/"+dval['signal']['outname']+"_exttrigger_nblocks"+str(NBLOCKS)+ \
        #                     "_packets" + str(PACKETS)+"_vped"+str(DEF_VPED) + \
        #                     "_delay450/13_results_signal_plots.png"
        results_signal_txt  = outfile_list[0].replace("_r0.tio","")+"/results_signal.txt"
        results_signal_html = outfile_list[0].replace("_r0.tio","")+"/results_signal.html"
        results_signal_png  = outfile_list[0].replace("_r0.tio","")+"/13_results_signal_plots.png"
        if (args.showtable_signal):
            if (platform == "darwin"):
                os.system(
                    "open -a firefox {0} &".format(results_signal_html))  # MAC
            if (platform == "linux" or platform == "linux2"):
                #os.system("firefox {0} &".format(results_signal_html))
                pass
        if (platform == "darwin"):
            os.system("open {0} &".format(results_signal_png))  # MAC
        if (platform == "linux" or platform == "linux2"):
            #os.system("eog {0} &".format(results_signal_png))
            pass
        
        test_status = checkpoint(
            checkpoint_name="Signal", checkpoint_question_enabled=CHECKPOINT_AFTER_SIGNAL,
            badchannels=ret, badchannels_threshold=MIN_BADCHANNELS_THRESHOLD_FOR_CHECKPOINT_SIGNAL
        )

    else:
        logger.log(logger.TEST_LEVEL_FAIL, "Signal test: FAILED.")
        exit(1)
    
    update_status_files(outdir=outdir, test=test_name, test_status=test_status)
    set_status_hmtl_directory(
        outdir=outdir,
        key="__SIGNAL_SUBDIR__",
        #subdir=dval['signal']['outname']+"_exttrigger_nblocks"+str(NBLOCKS)+ \
        #        "_packets" + str(PACKETS)+"_vped"+str(DEF_VPED) + \
        #        "_delay450",
        subdir=outfile_list[0].replace("_r0.tio","").split('/')[-1]
    )



if (ENABLE_LINEARITY):
    test_name, test_status = "linearity", False
    ## turn off the function generator just to check that agilent is connected
    if not args.disable_datataking:
        ret = -1
        logger.log(logger.TEST_LEVEL_INFO,
                   "Turning off the function generator, just to check communication.")
        try:
            #ret = agilent33250A_off()
            ret=0
        except:
            logger.exception(
                "Could not turn off the function generator output, exception occurred. Check if function generator is on and connection.")
            logger.log(logger.TEST_LEVEL_FAIL,
                       "Could not turn off the function generator output, exception occurred. Check if function generator is on and connection.")
            exit(1)

        if (ret == 0):
            logger.log(logger.TEST_LEVEL_INFO,
                       "Turn off the function generator: SUCCESS.")
        else:
            logger.log(logger.TEST_LEVEL_FAIL,
                       "Could not turn off the function generator output.")
            exit(1)
            
    if dval['smart']['flag_dac_loop']:
        dac_arg = dval['smart']['dacs_loop']
    else:
        dac_arg = dval['smart']['dacs']
    if dval['smart']['flag_globals_loop']:
        globals_arg = dval['smart']['globals_loop']
    else:
        globals_arg = dval['smart']['globals']

    args_linearity = argparse.Namespace(
        channel0=CHANNEL0,
        disable_analysis=args.disable_analysis,
        disable_datataking=args.disable_datataking,
        disable_summary=args.disable_summary,
        length=dval['linearity']['length'],
        module=args.module_number,
        moduletag=args.tag,
        nblocks=NBLOCKS, #dval['linearity']['nblocks'],
        nchannels=NCHANNELS,
        outdir=OUTDIR, #dval['linearity']['outdir'],
        outname=dval['linearity']['outname'],
        packets=PACKETS, #args.packets,
        peddatabase=None,
        pedname=dval['linearity']['pedname'],
        pedtrigtype=dval['pedestal']['triggertype'],
        signalfreq=PULSE_FREQ,
        signalscan=True,
        signalvals=dval['linearity']['signalvals'],
        triggerdelay=TRIGGERDELAY,
        triggertype=dval['linearity']['triggertype'],
        pmtref4=dval['linearity']['pmtref4'],
        thresh=dval['linearity']['thresh'],
        vped=DEF_VPED,
        force=False,
        enable_hv=dval['linearity']['hv_enable'],
        disable_smart_channels=dval['smart']['disable_channels'],
        smart_dacs=dac_arg,
        smart_global=globals_arg,
        smart_flag_dacs=dval['smart']['flag_dac_loop'],
        smart_flag_globals=dval['smart']['flag_globals_loop']
    )

    ret = -1  # initialize ret
    logger.log(logger.TEST_LEVEL_INFO, "Starting linearity test")
    try:
        ret, outfile_list = exec_signal_sipm(args_linearity)
    except:
        logger.exception(
            "Could not complete linearity test, an exception occurred (check log).")
        logger.log(logger.TEST_LEVEL_FAIL,
                   "Could not complete linearity run, an exception occurred (check log).")
        exit(1)

    if (ret>=0):  # ret == 0 if no channel is bad (nbad_ch=0)
        if not args.disable_summary:
            results_linearity_html = outdir + \
                                     "/linearity_summary_plots/summary_results_signal.html"
            results_linearity_png = outdir + "/linearity_summary_plots/linearity_summary.png"
            if (platform == "darwin"):
                os.system("open {0} &".format(results_linearity_png))  # MAC
            if (platform == "linux" or platform == "linux2"):
                os.system("eog {0} &".format(results_linearity_png))

            if (args.showtable_linearity):
                if (platform == "darwin"):
                    os.system(
                        "open -a firefox {0} &".format(results_linearity_html))  # MAC
                if (platform == "linux" or platform == "linux2"):
                    os.system("firefox {0} &".format(results_linearity_html))

            test_status = checkpoint(
                checkpoint_name="Linearity", checkpoint_question_enabled=CHECKPOINT_AFTER_LINEARITY,
                badchannels=ret, badchannels_threshold=MIN_BADCHANNELS_THRESHOLD_FOR_CHECKPOINT_LINEARITY
            )
    else:
        logger.log(logger.TEST_LEVEL_FAIL, "Linearity test: FAILED.")
        exit(1)

    update_status_files(outdir=outdir, test=test_name, test_status=test_status)
    set_status_hmtl_directory(
        outdir=outdir,
        key="__LINEARITY_SUBDIR__",
        subdir="linearity_summary_plots",
    )



if (ENABLE_VPED_SCAN):
    test_name, test_status = "vpedscan", False
    args_vpedscan = argparse.Namespace(
        channel0=CHANNEL0,
        disable_analysis=args.disable_analysis,
        disable_datataking=args.disable_datataking,
        disable_summary=args.disable_summary,
        length=dval['vpedscan']['length'],
        module=args.module_number,
        moduletag=args.tag,
        nblocks=NBLOCKS, #dval['vpedscan']['nblocks'],
        nchannels=NCHANNELS,
        outdir=OUTDIR, #dval['vpedscan']['outdir'],
        outname=dval['vpedscan']['outname'],
        packets=PACKETS, #args.packets,
        triggerdelay=TRIGGERDELAY,
        triggertype=dval['vpedscan']['triggertype'],
        fast_mode=dval['pedestal']['fast_mode'],
        vped=DEF_VPED,
        vpedscan=True,
        vpedvals=dval['vpedscan']['vpedvals'],
        force=False
    )  # 4100

    if not args.disable_datataking and PULSE_GENERATOR:
        ret = -1

        logger.log(logger.TEST_LEVEL_INFO,
                   "Turning off the function generator")
        try:

            ret = agilent33250A_off()
        except:
            logger.exception(
                "Could not turn off the function generator output, exception occurred. Check if function generator is on and connection.")
            logger.log(logger.TEST_LEVEL_FAIL,
                       "Could not turn off the function generator output, exception occurred. Check if function generator is on and connection.")
            exit(1)

        if (ret == 0):
            logger.log(logger.TEST_LEVEL_INFO,
                       "Turn off the function generator: SUCCESS.")
        else:
            logger.log(logger.TEST_LEVEL_FAIL,
                       "Could not turn off the function generator output.")
            exit(1)

    ret = -1
    logger.log(logger.TEST_LEVEL_INFO, "Starting Vped scan test")
    try:
        ret = exec_pedestal(args_vpedscan)  # ret = number of bad channels
    except:
        logger.exception(
            "Could not complete Vped scan run, an exception occurred (check log).")
        logger.log(logger.TEST_LEVEL_FAIL,
                   "Could not complete Vped scan run, an exception occurred (check log).")
        exit(1)

    if ret>=0 and not args.disable_summary:
        results_vped_html = outdir + \
                            "/vpedscan_summary_plot/summary_results_pedestal.html"
        results_vped_png = outdir + "/vpedscan_summary_plot/vpedscan_summary.png"
        if (platform == "darwin"):
            os.system("open {0} &".format(results_vped_png))  # MAC
        if (platform == "linux" or platform == "linux2"):
            os.system("eog {0} &".format(results_vped_png))

        if (args.showtable_vped):
            if (platform == "darwin"):
                os.system(
                    "open -a firefox {0} &".format(results_vped_html))  # MAC
            if (platform == "linux" or platform == "linux2"):
                os.system("firefox {0} &".format(results_vped_html))



    if (ret >=0):
        test_status = checkpoint(
            checkpoint_name="Vpedscan", checkpoint_question_enabled=CHECKPOINT_AFTER_VPEDSCAN,
            badchannels=ret, badchannels_threshold=MIN_BADCHANNELS_THRESHOLD_FOR_CHECKPOINT_VPEDSCAN
        )

    else:
        logger.log(logger.TEST_LEVEL_FAIL, "Vped scan test: FAILED.")
        exit(1)
    
    update_status_files(outdir=outdir, test=test_name, test_status=test_status)
    set_status_hmtl_directory(
        outdir=outdir,
        key="__VPEDSCAN_SUBDIR__",
        subdir="vpedscan_summary_plot",
    )

    


if (ENABLE_TRIGGER_SCAN):
    test_name, test_status = "triggerscan_pmtref4", False
    if not args.disable_datataking:
        ret = -1
        logger.log(logger.TEST_LEVEL_INFO,
                   "Setting up function generator for pulse injection for trigger rate scan over PMTRef4...")
        try:
            #ret = agilent33250A_inverted(
            #    PULSE_AMPLITUDE_VOLTS_TRIGGERSCAN_PMTREF4, PULSE_FREQ, PULSE_OFFSET, sync=False)
            ret=0
        except:
            logger.exception(
                "Could not set up the function generator for pulse injection for trigger rate scan over PMTRef4, an exception occurred (check log).")
            logger.log(logger.TEST_LEVEL_FAIL,
                       "Could not set up the function generator for pulse injection for trigger rate scan over PMTRef4, an exception occurred (check log).")
            exit(1)

        if (ret == 0):
            logger.log(logger.TEST_LEVEL_PASS,
                       "Set up pulse injection for trigger rate scan over PMTRef4: SUCCESS.")
        else:
            logger.log(logger.TEST_LEVEL_FAIL,
                       "Set up pulse injection for trigger rate scan over PMTRef4: FAILED.")
            exit(1)

    args_triggerscan_pmtref4 = argparse.Namespace(
        channel0=CHANNEL0,
        debug=False,
        disable_analysis=args.disable_analysis,
        disable_datataking=args.disable_datataking,
        force=False,
        gain=dval['trigscan_pmtref4']['gain'],
        groupsrange=GROUPSRANGE,
        #length=dval['trigscan_pmtref4']['length'],
        module=args.module_number,
        moduletag=args.tag,
        nblocks=NBLOCKS, #dval['trigscan_pmtref4']['nblocks'],
        nchannels=NCHANNELS,
        outdir=OUTDIR, #dval['trigscan_pmtref4']['outdir'],
        outname=dval['trigscan_pmtref4']['outname'],
        packets=PACKETS, #args.packets,
        pmtref4=dval['trigscan_pmtref4']['pmtref4'],
        pmtref4vals=[dval['trigscan_pmtref4']['pmtref4v_start'],
                     dval['trigscan_pmtref4']['pmtref4v_end'],
                     TRIGGERSCAN_PMTREF4_STEPSIZE],
        thresh=dval['trigscan_pmtref4']['thresh'],
        threshvals=None,
        external_trigger=dval['trigscan_pmtref4']['exttrig'],
        triggerdelay=dval['trigscan_pmtref4']['triggerdelay'],
        triggertype=dval['trigscan_pmtref4']['triggertype'],
        vped=DEF_VPED,
        vpedscan=False,
        vpedvals=[4000],#dval['trigscan_pmtref4']['vpedvals'],
        wbias=dval['trigscan_pmtref4']['wbias'],
        signalfreq=PULSE_FREQ,
        enable_sipm= dval['global']['enable_sipm'],
        enable_hv=dval['global']['hv_enable'],
        disable_smart_channels=dval['smart']['disable_channels'],
        smart_dacs=dval['smart']['dacs'],
        smart_global=dval['smart']['globals']
    )

    ret = -1
    logger.log(logger.TEST_LEVEL_INFO,
               "Starting trigger rate scan over PMTRef4")
    try:
        ret = exec_triggerscan(args_triggerscan_pmtref4)
        #ret = 0
    except:
        logger.exception(
            "Could not complete trigger rate scan over PMTref4, an exception occurred (check log).")
        logger.log(logger.TEST_LEVEL_FAIL,
                   "Could not complete trigger rate scan over PMTRef4, an exception occurred (check log).")
        exit(1)


    if (ret >= 0):
        test_status = checkpoint(
            checkpoint_name="Triggerscan PMTRef4", checkpoint_question_enabled=CHECKPOINT_AFTER_TRIGSCAN_PMTREF4,
            badchannels=ret, badchannels_threshold=MIN_BADCHANNELS_THRESHOLD_FOR_CHECKPOINT_TRIGSCAN_PMTREF4
        )
    else:
        logger.log(logger.TEST_LEVEL_FAIL, "Triggerscan PMTRef4 test: FAILED.")
        exit(1)

    update_status_files(outdir=outdir, test=test_name, test_status=test_status)
    set_status_hmtl_directory(
        outdir=outdir,
        key="__TRIGGERSCAN_PMTREF4_SUBDIR__",
        subdir="triggerscan_pmtref4_vped1200",
    )

    #if (ret == 0):
    #    logger.log(logger.TEST_LEVEL_PASS,
    #               "Trigger scan over PMTRef4: SUCCESS.")
    #else:
    #    logger.log(logger.TEST_LEVEL_FAIL,
    #               "Trigger scan over PMTRef4: FAILED.")
    #    exit(1)

    test_name, test_status = "triggerscan_thresh", False
    if not args.disable_datataking:
        ret = -1
        logger.log(logger.TEST_LEVEL_INFO,
                   "Setting up function generator for trigger rate scan over thresh...")
        try:
            #ret = agilent33250A_inverted(
            #    PULSE_AMPLITUDE_VOLTS_TRIGGERSCAN_THRESH, PULSE_FREQ, PULSE_OFFSET, sync=False)
            ret=0
        except:
            logger.exception(
                "Could not set up the function generator for trigger rate scan over thresh, an exception occurred (check log).")
            logger.log(logger.TEST_LEVEL_FAIL,
                       "Could not set up the function generator for trigger rate scan over thresh, an exception occurred (check log).")
            exit(1)

        if (ret == 0):
            logger.log(logger.TEST_LEVEL_PASS,
                       "Set up pulse injection for trigger rate scan over thresh: SUCCESS.")
        else:
            logger.log(logger.TEST_LEVEL_FAIL,
                       "Set up pulse injection for trigger rate scan over thresh: FAILED.")
            exit(1)

    args_triggerscan_thresh = argparse.Namespace(
        channel0=CHANNEL0,
        debug=False,
        disable_analysis=args.disable_analysis,
        disable_datataking=args.disable_datataking,
        force=False,
        gain=dval['trigscan_thr']['gain'],
        groupsrange=GROUPSRANGE,
        #length=dval['trigscan_thr']['length'],
        module=args.module_number,
        moduletag=args.tag,
        nblocks=NBLOCKS, #dval['trigscan_thr']['nblocks'],
        nchannels=NCHANNELS,
        outdir=OUTDIR, #dval['trigscan_thr']['outdir'],
        outname=dval['trigscan_thr']['outname'],
        packets=PACKETS, #args.packets,
        pmtref4=dval['trigscan_thr']['pmtref4'],
        pmtref4vals=None,
        thresh=2000, #dummy value
        threshvals=[dval['trigscan_thr']['threshv_start'],
                    dval['trigscan_thr']['threshv_end'],
                    TRIGGERSCAN_THRESH_STEPSIZE],
        external_trigger=dval['trigscan_thr']['exttrig'],
        triggerdelay=dval['trigscan_thr']['triggerdelay'],
        triggertype=dval['trigscan_thr']['triggertype'],
        vped=DEF_VPED,
        vpedscan=False,
        vpedvals=[4000], #dval['trigscan_thr']['vpedvals'],
        wbias=dval['trigscan_thr']['wbias'],
        signalfreq=PULSE_FREQ,
        enable_sipm= dval['global']['enable_sipm'],
        enable_hv=dval['global']['hv_enable'],
        disable_smart_channels=dval['smart']['disable_channels'],
        smart_dacs=dval['smart']['dacs'],
        smart_global=dval['smart']['globals']
    )

    ret = -1
    logger.log(logger.TEST_LEVEL_INFO,
               "Starting trigger rate scan over thresh parameter")
    try:
        ret = exec_triggerscan(args_triggerscan_thresh)
    except:
        logger.exception(
            "Could not complete trigger rate scan over thresh parameter, an exception occurred (check log).")
        logger.log(logger.TEST_LEVEL_FAIL,
                   "Could not complete trigger rate scan over thresh parameter, an exception occurred (check log).")
        exit(1)


    if (ret>=0):
        results_triggerscan_pmtref4_html = outdir + \
            "/triggerscan_pmtref4_vped1200/results_pmtref4_scan.html"
        results_triggerscan_thresh_html = outdir + \
            "/triggerscan_thresh_vped1200/results_thresh_scan.html"
        results_triggerscan_pmtref4_png1 = outdir + \
            "/triggerscan_pmtref4_vped1200/pmtref4_scan_peak_summary.png"
        results_triggerscan_pmtref4_png2 = outdir + \
            "/triggerscan_pmtref4_vped1200/pmtref4_scan_plateau_summary.png"
        results_triggerscan_thresh_png1 = outdir + \
            "/triggerscan_thresh_vped1200/thresh_scan_peak_summary.png"
        results_triggerscan_thresh_png2 = outdir + \
            "/triggerscan_thresh_vped1200/thresh_scan_plateau_summary.png"
        if (platform == "darwin"):
            os.system("open {0} &".format(results_triggerscan_pmtref4_png1))  # MAC
            os.system("open {0} &".format(results_triggerscan_pmtref4_png2))  # MAC
            os.system("open {0} &".format(results_triggerscan_thresh_png1))  # MAC
            os.system("open {0} &".format(results_triggerscan_thresh_png2))  # MAC
        if (platform == "linux" or platform == "linux2"):
            os.system("eog {0} &".format(results_triggerscan_pmtref4_png1))
            os.system("eog {0} &".format(results_triggerscan_pmtref4_png2))
            os.system("eog {0} &".format(results_triggerscan_thresh_png1))
            os.system("eog {0} &".format(results_triggerscan_thresh_png2))

        if (args.showtable_triggerscan):
            if (platform == "darwin"):
                os.system("open -a firefox {0} &".format(results_triggerscan_pmtref4_html))  # MAC
                os.system("open -a firefox {0} &".format(results_tirggerscan_thresh_html))  # MAC
            if (platform == "linux" or platform == "linux2"):
                os.system("firefox {0} &".format(results_triggerscan_pmtref4_html))
                os.system("firefox {0} &".format(results_triggerscan_thresh_html))






    if ret >= 0:
       test_status = checkpoint(
           checkpoint_name="Triggerscan thresh", checkpoint_question_enabled=CHECKPOINT_AFTER_TRIGSCAN_THR,
           badchannels=ret, badchannels_threshold=MIN_BADCHANNELS_THRESHOLD_FOR_CHECKPOINT_TRIGSCAN_THR
       )
    else:
        logger.log(logger.TEST_LEVEL_FAIL, "Triggerscan thresh test: FAILED.")
        exit(1)
    
    update_status_files(outdir=outdir, test=test_name, test_status=test_status)
    set_status_hmtl_directory(
        outdir=outdir,
        key="__TRIGGERSCAN_THRESH_SUBDIR__",
        subdir="triggerscan_thresh_vped1200",
    )

if not args.disable_summary:
    status_html = outdir + "/status.html"
    if (platform == "darwin"):
        os.system("open -a firefox {0} &".format(status_html))  # MAC
    if (platform == "linux" or platform == "linux2"):
        os.system("firefox {0} &".format(status_html))
        
    #if (ret == 0):
    #    logger.log(logger.TEST_LEVEL_PASS,
    #               "Trigger rate scan over thresh: SUCCESS.")
    #else:
    #    logger.log(logger.TEST_LEVEL_FAIL,
    #               "Trigger rate scan over thresh: FAILED.")
    #    exit(1)
