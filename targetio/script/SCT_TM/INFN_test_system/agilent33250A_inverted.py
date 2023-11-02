#!/usr/bin/env python

from agilent33250A_utils import *
import sys
import argparse
from MyLogging import logger
from utils import *

def agilent33250A_inverted(ampl, freq, offs, sync=True):
    f = agilent33250A("/dev/ttyS0")

    max_retries = 5

    success = False
    for i in range(max_retries):
      f.send ("OUTPUT OFF")
      time.sleep(0.1)
      f.send ("OUTPUT?")
      if f.check_int(0):
        logger.log(logger.TEST_LEVEL_INFO, "Failed to turn off the output, retrying (" + str(i) + ")")
        time.sleep(1);
        continue
      else: success = True; break
    if not success: return 1

    success = False
    for i in range(max_retries):
      f.send("OUTPUT:POLARITY INVERTED")
      time.sleep(0.1)
      f.send("OUTPUT:POLARITY?")
      if f.check_string("INV"):
        logger.log(logger.TEST_LEVEL_INFO, "Failed to set polarity to inverted, retrying (" + str(i) + ")")
        time.sleep(1);
        continue
      else: success = True; break
    if not success: return 1


    success = False
    for i in range(max_retries):
      f.send("FUNC PULSE")
      time.sleep(0.1)
      f.send("FUNC?")
      if f.check_string("PULS"):
        logger.log(logger.TEST_LEVEL_INFO, "Failed to set pulse mode, retrying (" + str(i) + ")")
        time.sleep(1);
        continue
      else: success = True; break
    if not success: return 1


    success = False
    for i in range(max_retries):
      f.send("PULSE:WIDTH 8e-9")
      time.sleep(0.5)
      f.send("PULSE:WIDTH?")
      if f.check_float(8e-9):
        logger.log(logger.TEST_LEVEL_INFO, "Failed to set pulse width, retrying (" + str(i) + ")")
        time.sleep(1);
        continue
      else: success = True; break
    if not success: return 1


    success = False
    for i in range(max_retries):
      f.send("PULSE:TRANSITION 5e-9")
      time.sleep(0.5)
      f.send("PULSE:TRANSITION?")
      if f.check_float(5e-9):
        logger.log(logger.TEST_LEVEL_INFO, "Failed to set pulse transition time, retrying (" + str(i) + ")")
        time.sleep(1);
        continue

      else: success = True; break
    if not success: return 1


    success = False
    for i in range(max_retries):
      f.send("BURS:STAT OFF")
      time.sleep(0.1)
      f.send("BURS:STAT?")
      if f.check_int(0):
        logger.log(logger.TEST_LEVEL_INFO, "Failed to disable burst mode, retrying (" + str(i) + ")")
        time.sleep(1);
        continue
      else: success = True; break
    if not success: return 1


    success = False
    for i in range(max_retries):
      f.send("FREQ " + str(freq))
      time.sleep(0.5) ### 
      f.send("FREQ?")
      if f.check_float(freq):
        logger.log(logger.TEST_LEVEL_INFO, "Failed to set pulse frequency, retrying (" + str(i) + ")")
        time.sleep(1);
        continue
      else: success = True; break
    if not success: return 1


    success = False
    for i in range(max_retries):
      f.send("VOLT " + str(ampl))
      time.sleep(0.1)
      f.send("VOLT?")
      if f.check_float(ampl):
        logger.log(logger.TEST_LEVEL_INFO, "Failed to set pulse amplitude, retrying (" + str(i) + ")")
        time.sleep(1);
        continue
      else: success = True; break
    if not success: return 1


    time.sleep(0.1)

    success = False
    for i in range(max_retries):
      f.send("VOLT:OFFS " + str(offs))
      time.sleep(0.1)
      f.send("VOLT:OFFS?")
      if f.check_float(offs):
        logger.log(logger.TEST_LEVEL_INFO, "Failed to set pulse offset, retrying (" + str(i) + ")")
        time.sleep(1);
        continue
      else: success = True; break
    if not success: return 1


    if sync:
        success = False
        for i in range(max_retries):
          f.send("OUTP:SYNC ON")
          time.sleep(0.1)
          f.send("OUTP:SYNC?")
          if f.check_int(1):
            logger.log(logger.TEST_LEVEL_INFO, "Failed to enable sync output, retrying (" + str(i) + ")")
            time.sleep(1);
            continue

          else: success = True; break
        if not success: return 1

    else:
        success = False
        for i in range(max_retries):
          f.send("OUTP:SYNC OFF")
          time.sleep(0.1)
          f.send("OUTP:SYNC?")
          if f.check_int(0):
            logger.log(logger.TEST_LEVEL_INFO, "Failed to disable sync output, retrying (" + str(i) + ")")
            time.sleep(1);
            continue
          else: success = True; break
        if not success: return 1


    success = False
    for i in range(max_retries):
      f.send ("OUTPUT ON")
      time.sleep(0.1)
      f.send ("OUTPUT?")
      if f.check_int(1):
            logger.log(logger.TEST_LEVEL_INFO, "Failed to enable output, retrying (" + str(i) + ")")
            time.sleep(1);
            continue
      else: success = True; break
    if not success: return 1

    return 0

def main():

   parser = argparse.ArgumentParser()
   parser.add_argument("amplitude", help="amplitude of the pulse from 0.0005 to 10, units: Volt")
   parser.add_argument("frequency", help="frequency of pulse repetition in Hz")
   parser.add_argument("-d", "--terminal-debug-level", help="debug level for terminal output",
      choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL','TEST_INFO','TEST_PASS','TEST_FAIL'], default='TEST_INFO')
   parser.add_argument("-dbg" ,"--debug", help="flag to enable debug messages on console", action="store_true")

   args = parser.parse_args()


   ampl = args.amplitude
   freq = args.frequency
   offs = 0

   logger.setup(logname="Agilent_inverted", logfile=unique_filename("./agilent_inverted.log"), debug_mode = args.debug)

   ret = 1
   try:
     ret = agilent33250A_inverted(ampl, freq, offs)
   except:
     logger.exception("Could not setup the function generator, exception occurred, check connection.")
     logger.log(logger.TEST_LEVEL_FAIL, "Could not setup the function generator, check connection.")
     return 1

   if (ret == 1):
     logger.log(logger.TEST_LEVEL_FAIL, "Setup the function generator for pulses: FAIL")
     return 1


   logger.log(logger.TEST_LEVEL_PASS, "Setup the function generator for pulses: SUCCESS.")
   return 0




if __name__ == "__main__":
    exit(main())
