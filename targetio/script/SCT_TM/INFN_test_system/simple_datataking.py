import target_driver
import target_io
import time
from astropy.io import ascii
import os
import sys
import argparse

from TC_utils import TCModule



if __name__=="__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-v" ,"--vped", help="Vped to use", type=int, default=1200)
	parser.add_argument("-b" ,"--nblocks", help="number of Blocks of 32 samples", type=int, default=8)
	#parser.add_argument("-t" ,"--tag", help="tag to append to output file name", type=str, default="")
	parser.add_argument("-o" ,"--outfile", help="output file name", type=str, default="file_r0.tio")
	parser.add_argument("-D" ,"--outdir", help="output directory name", type=str, default="./")
	parser.add_argument("-l" ,"--length", help="test duration in seconds", type=float, default=10)

	parser.add_argument("-t" ,"--triggertype", help="trigger type: 0=internal, 1=external, 2=hardsync", type=int, default=2)
	parser.add_argument("-d" ,"--triggerdelay", help="triggerdelay", type=int, default=364)

	args = parser.parse_args()

	outdir = args.outdir
	outfile = outdir+"/"+args.outfile
	print("Output file:", outfile)

	#VPED_FILE = "/media/cta/157bfe11-9587-4947-8a3e-1e814c5c25dc/Messungen_Stefan/Config/Vpeds.txt"
	#VTRIM_FILE = "/media/cta/157bfe11-9587-4947-8a3e-1e814c5c25dc/Messungen_Stefan/Config/vtrim_scan.txt"

	#my_ip = "192.168.12.1"
	my_ip = "192.168.12.3"
	module_ip = "192.168.12.173"
	reset = True

	moduleTC = ModuleTC(my_ip = "192.168.12.3", module_ip = "192.168.12.173", reset=True)


	nblocks = int(args.nblocks)
	daq_time = args.length
        triggerdelay = int(args.triggerdelay)
	print("Number of blocks:",nblocks)

	vped=int(args.vped) # standard value
	sst = 58 # standard value
	vtrim=1240 # standard value


	moduleTC.set_Vpeds(vped_file=None, vped=vped) 
        moduleTC.set_SSToutFB_Vtrim(vtrim_file=None, vtrim=vtrim, sstoutfb=sst)


        triggertype = args.triggertype 
	moduleTC.prepare_daq(asics=None, nblocks = nblocks, triggerdelay=triggerdelay, packet_event=4, triggertype=triggertype, warmup_time=5)
        moduleTC.daq(outfile, daq_time=daq_time, delay_loop=False) 

        moduleTC.close()




