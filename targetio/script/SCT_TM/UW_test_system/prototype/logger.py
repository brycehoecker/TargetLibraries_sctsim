# Brent Mode
# Created on 08 July 2019
# Create a log file for each data run.

import csv
import datetime
import os
import sys

def log(date_obj, signal_type, period, width, ampl, offset, module, req):
    homedir = os.environ['HOME']
    outdir = "{}/prototype/log/".format(homedir)
    filename = "{}".format(outdir) + "log_{:%Y_%m}".format(date_obj) + ".log"

    if not os.path.exists('{}/target5and7data'.format(homedir)):
        print('Data directory target5and7data is not mounted. Mount and try again.')
        raise SystemExit

    runfilename = '{}/target5and7data/previousRun.txt'.format(homedir)
    file = open(runfilename, 'r')
    previousRun = int(file.read())
    file.close()
    runID = previousRun + 1
    file = open(runfilename, 'w')
    file.write('{}'.format(runID))
    file.close()

    with open (filename, 'a') as f:
        if os.stat(filename).st_size == 0:
            writer = csv.writer(f)
            writer.writerow(['Run', 'Date', 'Time', 'Signal_Type', 'Period(ns)', 'Pulse_Width(ns)', 'Amplitude(mV)', 'Offset(mv)', 'Module', 'Requirement'])
            writer.writerow([runID, '{:%y_%m_%d}'.format(date_obj), '{:%H_%M_%S}'.format(date_obj), signal_type, period,
                width, ampl, offset, module, req])
        else:
            writer = csv.writer(f)
            writer.writerow([runID, '{:%y_%m_%d}'.format(date_obj), '{:%H_%M_%S}'.format(date_obj), signal_type, period,
                width, ampl, offset, module, req])

    datafile = "{}/target5and7data/run{}.fits".format(homedir, runID)
    return datafile

