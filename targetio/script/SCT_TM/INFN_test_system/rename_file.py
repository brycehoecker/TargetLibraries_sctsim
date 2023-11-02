import numpy as np
import os, sys
from MyLogger import logger

#fname = "testing/Module2_191008/signal_aux_exttrigger_signal{0:.1f}_nblocks4_packets4_vped1200_delay450_r0.tio"
#newfname = "testing/Module2_191008/signal_aux_exttrigger_signal{0:.4f}_nblocks4_packets4_vped1200_delay450_r0.tio"
fname = "testing/Module2_191008/signal_pri_exttrigger_signal{0}_nblocks4_packets4_vped1200_delay450_r0.tio"
newfname = "testing/Module2_191008/signal_pri_exttrigger_signal{0:.4f}_nblocks4_packets4_vped1200_delay450_r0.tio"

vals = np.arange(0.2,5.0,0.2)
logger.info("Vals= " + str(vals))
cmd = "mv {0} {1}"

for v in vals:
	fname1 = fname.format(v)
	newfname1 = newfname.format(v)
	print(cmd.format(fname1,newfname1))
