#!/usr/bin/env python

from agilent33250A_utils import *
import argparse
from MyLogging import logger
from utils import *



def agilent33250A_off(serial_port="/dev/ttyS0"):
    f = agilent33250A(serial_port)

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
    if success: return 0
    else: return 1

def main():

   parser = argparse.ArgumentParser()
   parser.add_argument("-d", "--terminal-debug-level", help="debug level for terminal output",
      choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL','TEST_INFO','TEST_PASS','TEST_FAIL'], default='TEST_INFO')
   parser.add_argument("-dbg" ,"--debug", help="flag to enable debug messages on console", action="store_true")


   args = parser.parse_args()

   logger.setup(logname="Agilent_inverted", logfile=unique_filename("./agilent_off.log"), debug_mode = args.debug)



   ret = 1
   try:
     ret = agilent33250A_off()
   except:
     logger.exception("Could not turn off the function generator output, exception occurred, check connection.")
     logger.log(logger.TEST_LEVEL_FAIL, "Could not turn off the function generator output, check connection.")
     return 1

   if (ret == 0):
     logger.log(logger.TEST_LEVEL_PASS, "Turn off the function generator: SUCCESS.")
     return 0
   else:
     logger.log(logger.TEST_LEVEL_FAIL, "Could not turn off the function generator output.")
     return 1


if __name__ == "__main__":
    result = main()
    exit(result)
