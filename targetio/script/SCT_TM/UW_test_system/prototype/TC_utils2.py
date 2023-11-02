import target_driver
import target_io
import target_calib
import time
from astropy.io import ascii
import os
import sys
import argparse
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('whitegrid')
colors = sns.color_palette('deep')

def generate_ped(fname):
        tmp_fname, ext = os.path.splitext(fname)
        new_ext = ".tcal"

        if tmp_fname.find("_r0")>=0:
                outfname = tmp_fname.replace("_r0","_peddb")+new_ext
        elif tmp_fname.split("/")[-1].startswith("r0"):
                toks = tmp_fname.split("/")
                path = "/".join(toks[:-1])+"/"
                outfname = path+toks[-1].replace("r0","peddb",1)+new_ext
        else:
                outfname = tmp_fname+"_peddb"+new_ext

        if not os.path.exists(outfname):
                cmd = "generate_ped -i {0} -o {1}".format(fname, outfname)
                print (cmd)
                os.system(cmd)
        return outfname

def apply_calibration(fname, pedfname):
        if fname.find("_r0")>=0:
                outfname = fname.replace("_r0","_r1")
        elif fname.split("/")[-1].startswith("r0"):
                toks = fname.split("/")
                path = "/".join(toks[:-1])+"/"
                outfname = path+toks[-1].replace("r0","r1",1)
        else:
                tmp, ext = os.path.splitext(fname)
                outfname = tmp+"_r1"+ext
        cmd = "apply_calibration -i {0} -p {1} -o {2}".format(fname, pedfname, outfname)
        print (cmd)
        os.system(cmd)
        return outfname


class Waveform:
        def __init__(self):
                self.isR1 = False
                self.filename = None
                self.reader = None
                self.n_pixels = 0
                self.n_samples = 0
                self.n_events = 0
                self.first_cell_ids = None
                self.waveforms = None

        def read_data(self, filename):
                self.filename = filename
                self.reader = target_io.WaveformArrayReader(filename)
                self.isR1 = self.reader.fR1
                self.n_pixels = self.reader.fNPixels
                self.n_samples = self.reader.fNSamples
                self.n_events = self.reader.fNEvents
                self.first_cell_ids = np.zeros((self.n_events,self.n_pixels),dtype=np.uint16)

                #Generate the memory to be filled in-place
                if self.isR1:
                        self.waveforms = np.zeros((self.n_events,self.n_pixels, self.n_samples), dtype=np.float32)
                        #for event_index in tqdm(range(0,self.n_events)):
                        #        self.reader.GetR1Event(event_index,self.waveforms[event_index],self.first_cell_ids[event_index])
                        self.reader.GetR1Events(0,self.waveforms,self.first_cell_ids)

                else:
                        self.waveforms = np.zeros((self.n_events,self.n_pixels, self.n_samples),dtype=np.ushort)   #needed for R0 data
                        for event_index in tqdm(range(0,self.n_events)):
                                self.reader.GetR0Event(event_index,self.waveforms[event_index],self.first_cell_ids[event_index])
                                #current_cpu_ns = self.reader.fCurrentTimeNs
                                #current_cpu_s = self.reader.fCurrentTimeSec
                                #tack_timestamp = self.reader.fCurrentTimeTack
                                #cpu_timestamp = ((current_cpu_s * 1E9) + np.int64(current_cpu_ns))/1000000
                                #have the cpu timestamp in some nice format
                                #t_cpu = pd.to_datetime(np.int64(current_cpu_s * 1E9) + np.int64(current_cpu_ns),unit='ns')

if __name__ == '__main__':
    pedfile = sys.argv[1]
    wf = Waveform()
    wf.read_data(pedfile)
    nmodules = 1
    nmaxblocks = 512
    pedmaker = target_calib.PedestalMaker(nmodules, nmaxblocks, wf.n_samples, False)
    for ievt in range(wf.n_events):
        pedmaker.AddEvent(wf.waveforms[ievt,:,:], wf.first_cell_ids[ievt,:])
    pedmaker.Save('pedestal_database.tcal', False)

    peddata = 'pedestal_database.tcal'
    sigdata = sys.argv[2]
    caldata = apply_calibration(sigdata, peddata)

    calreader = target_io.WaveformArrayReader(caldata)
    n_pixels = calreader.fNPixels
    n_samples = calreader.fNSamples
    n_events = calreader.fNEvents

    waveforms = np.zeros((n_pixels, n_samples), dtype=np.float32)

    first_cell_ids = np.zeros(n_pixels, dtype=np.uint16)

    all_waveforms = [] #np.array((n_events, 64, 256), dtype=np.float32)

    for event_index in range(0, n_events):#tqdm(range(0, n_events)):
        calreader.GetR1Event(event_index, waveforms, first_cell_ids)
        plt.plot(waveforms[28])
        mean_noise = np.mean(waveforms[28])
        sigma = np.std(waveforms[28])
        print('Mean: {}\nSigma: {}'.format(mean_noise, sigma))
        all_waveforms.append(waveforms)
        """
        plt.plot([0, 256], [mean_noise, mean_noise], linestyle='--', color=colors[1])
        plt.xlabel('Time (ns)')
        plt.ylabel('Calibrated Waveform (ADC Counts)')
        plt.title('Pedestal Subtracted Pedestal Data\nSingle Event')
        plt.savefig('CAL_TRIAL.pdf')
        """
    all_waveforms = np.array(all_waveforms)
    for ch in range(64):
        np.savez('calData_ch_{}_crosstalk'.format(ch), waveforms=all_waveforms[:,ch,:])

    plt.savefig('CAL_TRIAL.pdf')
    """
    calwf = Waveform()
    calwf.read_data(caldata)
    plt.plot(calwf.waveforms[32])
    plt.savefig('CAL_TRIAL.pdf')
    """
