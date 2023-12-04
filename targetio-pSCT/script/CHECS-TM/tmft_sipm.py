import target_driver
import target_io
from CHECLabPy.core.io import TIOReader
import time
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import colors
from tqdm import tqdm
import sys
import argparse
from argparse import ArgumentDefaultsHelpFormatter as Formatter
import datetime
from math import factorial
    
#################################################
# CHEC-S TARGET Module functionality test script
#
# Connect to TM, setup for for data taking, enable
# HV, measure HV, read slow values,
# acquire data to file, plot data, repeat the loop,
# disable HV
#
#          Version 0i - August 2018
#   RW, CD, hacked from:
#   Steve Leach, University of Leicester
# 
# usage: python tmft_realtime_takedata_v0h.py 0
##################################################

'''
Todo:

* Subtract pedestal?
* Gain match?

'''


def savitzky_golay(y, window_size, order, deriv=0, rate=1):
  try:
    window_size = np.abs(np.int(window_size))
    order = np.abs(np.int(order))
  except ValueError(msg):
    raise ValueError("window_size and order have to be of type int")
  if window_size % 2 != 1 or window_size < 1:
    raise TypeError("window_size size must be a positive odd number")
  if window_size < order + 2:
    raise TypeError("window_size is too small for the polynomials order")
  order_range = range(order+1)
  half_window = (window_size -1) // 2
  # precompute coefficients
  b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
  m = np.linalg.pinv(b).A[deriv] * rate**deriv * factorial(deriv)
  # pad the signal at the extremes with
  # values taken from the signal itself
  firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
  lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
  y = np.concatenate((firstvals, y, lastvals))
  return np.convolve( m[::-1], y, mode='valid')



def setup_tm(my_ip='192.168.12.1', tm_ip='192.168.12.176', delay=300):
  vpedbias = 1100 #DAC offset value, 0:4096
  vped_ = 1200 #real 0:4096, 0 to lower the ped, 4096 higher ped
  PMTref4 = 0#1800
  thresh  = 0
  nblocks = 10 #data blocks to capture, 0:14	
  nmaxchan = 1 #so many channels come in one packet

  
  nsdeadtime = 0 #62500
  sr_disabletrigger = 1 # disable further triggers during a readout, 0:1

  # triggerdelay = 425 # Value needed in thermal chamber
  triggerdelay = delay# was270 # delay to wait before readout of waveform***, 0:32767, ns

  module_def = "/home/cta/Software/TargetDriver/trunk/config/TC_MSA_FPGA_Firmware0xC0000008.def"
  asic_def = "/home/cta/Software/TargetDriver/trunk/config/TC_ASIC.def"
  trigger_asic_def = "/home/cta/Software/TargetDriver/trunk/config/T5TEA_ASIC.def"

  tm = target_driver.TargetModule(module_def, asic_def, trigger_asic_def, 0)
  tm.EstablishSlowControlLink(my_ip, tm_ip)
  tm.Initialise()
  ret, fw = tm.ReadRegister(0)
  print ("\nFirmware version: {:x}".format(fw))
  tm.EnableDLLFeedback()

  ip = False #have to power cycle after setting new IP

  if ip:

    new_ip_suffix = 122
    new_ip = "192.168.12." + str(new_ip_suffix)
    check_ip = tm.ReadModuleIP()
    print("Readback IP", str(check_ip))
    tm.ModifyModuleIP(new_ip_suffix)
    print ("Setting IP address from ", tm_ip, " to ", new_ip)
    check_ip = tm.ReadModuleIP()
    print("Readback IP", str(check_ip))
    exit()

  print ("\nmodule initialized\n")

  # Disable trigger
  tm.WriteSetting("TACK_EnableTrigger", 0)
  tm.DisableHVAll()

  ######### Read firmware version #############
  ret, fw = tm.ReadRegister(0)
  print ("\nFirmware version: {:x}".format(fw))

  tm.WriteTriggerASICSetting("VpedBias",0, vpedbias,True)
  tm.WriteTriggerASICSetting("VpedBias",1, vpedbias,True)
  tm.WriteTriggerASICSetting("VpedBias",2, vpedbias,True)
  tm.WriteTriggerASICSetting("VpedBias",3, vpedbias,True)

  for channel in range(16):
      tm.WriteTriggerASICSetting("Vped_{}".format(channel),0,vped_,True) # ASIC 0
      tm.WriteTriggerASICSetting("Vped_{}".format(channel),1,vped_,True) # ASIC 1
      tm.WriteTriggerASICSetting("Vped_{}".format(channel),2,vped_,True) # ASIC 2
      tm.WriteTriggerASICSetting("Vped_{}".format(channel),3,vped_,True) # ASIC 3

  ######### Enable the channels and settings #############
  tm.WriteSetting("EnableChannelsASIC0", 0b1111111111111111) # Enable or disable 16 channels
  tm.WriteSetting("EnableChannelsASIC1", 0b1111111111111111)
  tm.WriteSetting("EnableChannelsASIC2", 0b1111111111111111)
  tm.WriteSetting("EnableChannelsASIC3", 0b1111111111111111)

  tm.WriteSetting("Zero_Enable", 0x1) #data trasnfer, leave at 1?
  tm.WriteSetting("DoneSignalSpeedUp",0) #digitiser ramp stop, needed for high rates only?
  tm.WriteSetting("NumberOfBlocks", nblocks)
  tm.WriteSetting("MaxChannelsInPacket", nmaxchan)

  #tm.WriteASICSetting("Vdischarge",2, 1000,True)
  #tm.WriteASICSetting("Isel",2, 1700,True)
  tm.WriteRegister(0x5f,nsdeadtime)
  tm.WriteSetting("SR_DisableTrigger",sr_disabletrigger)

  ######### Set PMTref and thresholds #############
  # Thresh sets the threshold, it's inverted so 0 is the maximum
  tm.WriteTriggerASICSetting("PMTref4_0",0,PMTref4,True) #
  tm.WriteTriggerASICSetting("Thresh_0",0,thresh,True)

  ######### Setup triggering ################
  # Trigger info:
  # For External clocked pulse to trigger (Pulse, 10ms period, 2V, width <10us)
  #	ExtTriggerDirection=0, TACK_EnableTrigger=0x10000
  tm.WriteSetting("TriggerDelay", triggerdelay) # lookback time between instant when the trigger is issued and the portion of the ASIC storage to digitize

  return tm



def take_data(my_ip, tm, fname, hvon=False, hvdac=150, sleep=2): #'r0.tio'):

  if hvon:
    for i in range(16):
      if i == 0: hvdac =  87
      elif i == 1: hvdac = 79
      elif i==2: hvdac = 84
      elif i == 3: hvdac = 72
      elif i==4: hvdac = 83
      elif i == 5: hvdac = 87
      elif i==6: hvdac = 105
      elif i == 7: hvdac = 79
      elif i==8: hvdac = 87
      elif i == 9: hvdac = 88
      elif i==10: hvdac = 103
      elif i==11: hvdac = 98
      elif i == 12: hvdac = 82
      elif i==13: hvdac = 89
      elif i == 14: hvdac = 81
      elif i==15: hvdac = 85
      
      tm.SetHVDAC(i, hvdac) # superpixel 0 to 15
    tm.SetHVDACAll(40)  
    print ("Turn on HV and let settle.....\n")
    tm.EnableHVAll()
    time.sleep(1)  # wait

  ######### Setup the data transfer #############
  kNPacketsPerEvent = 64 # by default we have a data packet for each channel, this can be changed
  nblocks = 10 #data blocks to capture, 0:14
  nmaxchan = 1 #so many channels come in one packet
  kPacketSize = target_driver.DataPacket_CalculatePacketSizeInBytes(nmaxchan, 32 * (nblocks + 1))
  kBufferDepth = 1000

  listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
  listener.AddDAQListener(my_ip)
  listener.StartListening()
  writer = target_io.EventFileWriter(fname, kNPacketsPerEvent, kPacketSize)
  buf = listener.GetEventBuffer()
  writer.StartWatchingBuffer(buf)

  print ("\nAcquiring data...\a")
  tm.WriteSetting("TACK_TriggerType", 0x0)
  tm.WriteSetting("TACK_TriggerMode", 0x0)
  #trigger direction (1=hardsync,0=external)
  tm.WriteSetting("ExtTriggerDirection", 0x1)
  tm.WriteSetting("TACK_EnableTrigger", 0x10000) #
  #tm.WriteSetting("TACK_EnableTrigger", 0b10000000000000000) #
   
  time.sleep(sleep)

  ######### Stop data taking ###################
  
  tm.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers

  writer.StopWatchingBuffer()  # stops data storing in file
  buf.Flush()
  print ("Output file: {}\a".format(fname))
  writer.Close()

  tm.WriteSetting("ExtTriggerDirection", 0x0)  # restores hard trigger from external source
  tm.SetHVDACAll(255) #set all HV DACs low value (255 is minimum)
  tm.DisableHVAll()
  #tm.CloseSockets()

'''
def plot_HV_Groups(fname_r0):
loop from pixel 0 - 64
	average first 32 samples of each event and remove from wf (baseline subtraction)
loop through all pixels 
	plot four pixels in each HV group on one plot 
	save plot with global pixel numbers 
#use plots to determine whether pixels are broken or not 
'''


def set_fonts(sizes = [6]):
    if len(sizes) > 0:
        plt.rcParams["font.size"] = sizes[0]

    if len(sizes) > 1:
        plt.rcParams["axes.titlesize"] = sizes[1]
    else:
        plt.rcParams["axes.titlesize"] = sizes[0]

    if len(sizes) > 2:
        plt.rcParams["axes.labelsize"] = sizes[2]
    else:
        plt.rcParams["axes.labelsize"] = sizes[0]

    if len(sizes) > 3:
        plt.rcParams["legend.fontsize"] = sizes[3]
    else:
        plt.rcParams["legend.fontsize"] = sizes[0]

    if len(sizes) > 3:
        plt.rcParams["xtick.labelsize"] = sizes[4]
        plt.rcParams["ytick.labelsize"] = sizes[4]
    else:
        plt.rcParams["xtick.labelsize"] = sizes[0]
        plt.rcParams["ytick.labelsize"] = sizes[0]



def make_avwf(fname_r0):
  r0 = TIOReader(fname_r0)
  nev = r0.n_events
  print ("Number of events in file = %i" % nev)
  avwf = np.zeros((64,r0.n_samples))
  for iev in range(nev):
     wf = r0[10]#iev]
     avwf += wf
  avwf/=r0.n_events
  for pix in range(len(avwf)):
    avwf[pix] -= np.mean(avwf[pix, 0:40])
  # Close r0!
  return avwf



def make_plots(avwf, tile, sn):
  fname_pdf = 'TM26_SiPMTile%02i.pdf' % (tile)
  #fname_pdf = 'TM26_SiPMTile%02i_%10i_pattern.pdf' % (tile, sn)
  pdf = PdfPages(fname_pdf)

  set_fonts([6,6,6,4,6,6])
  plot_wf_sp(pdf, avwf, "Tile %02i\nWaveforms grouped by SP" % (tile), tile)
  set_fonts([8,8,8,8,8,8])
  plot_wf(pdf, avwf, tile)

  d = pdf.infodict()
  d['Title'] = 'CHEC-S SiPM Tile Plots'
  d['Author'] = u'C Duffy'
  d['Subject'] = ''
  d['Keywords'] = 'CHEC, SiPM'
  d['CreationDate'] = datetime.datetime.today()
  d['ModDate'] = datetime.datetime.today()
  pdf.close()



def take_pedestal(my_ip, tm, fname_ped):
  
  tm.SetHVDACAll(255) #set all HV DACs low value (255 is minimum)
  
  ######### Setup the data transfer #############
  kNPacketsPerEvent = 64 # by default we have a data packet for each channel, this can be changed
  nblocks = 3 #data blocks to capture, 0:14
  nmaxchan = 1 #so many channels come in one packet
  kPacketSize = target_driver.DataPacket_CalculatePacketSizeInBytes(nmaxchan, 32 * (nblocks + 1))
  kBufferDepth = 1000

  listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
  listener.AddDAQListener(my_ip)
  listener.StartListening()
  writer = target_io.EventFileWriter(fname_ped, kNPacketsPerEvent, kPacketSize)
  buf = listener.GetEventBuffer()
  writer.StartWatchingBuffer(buf)

  print ("\nAcquiring data...\a")
  tm.WriteSetting("TACK_TriggerType", 0x0)
  tm.WriteSetting("TACK_TriggerMode", 0x0)
  tm.WriteSetting("ExtTriggerDirection", 0x1)
  tm.WriteSetting("TACK_EnableTrigger", 0x10000) #
  #tm.WriteSetting("TACK_EnableTrigger", 0b10000000000000000) #
   
  time.sleep(1000)

  ######### Stop data taking ###################
  tm.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers

  writer.StopWatchingBuffer()  # stops data storing in file
  buf.Flush()
  print ("Output file: {}\a".format(fname_ped))
  writer.Close()

  tm.WriteSetting("ExtTriggerDirection", 0x0)  # restores hard trigger from external source
  tm.SetHVDACAll(255) #set all HV DACs low value (255 is minimum)
  tm.DisableHVAll()
  tm.CloseSockets()



def subtract_pedestal(avwf, fname_ped):
  r0 = TIOReader(fname_ped)
  nev = r0.n_events
  #print ("Number of events in file = %i" % nev)
  avped = np.zeros((64,r0.n_samples))
  for iev in range(nev):
     ped = r0[iev]
     avped += ped
  avped/=r0.n_events
  for pix in range(len(avped)):
    avped[pix] -= np.mean(avped[pix, 0:40])
  
  subt_avwf = avwf-avped    
  return subt_avwf



def plot_wf(pdf, wf, tile):
  nsam = len(wf[0])  
  meanwf = np.mean(wf, axis=0)
  min = np.min(np.min(wf))
  max = np.max(np.max(wf))*1.5
  meanpeak = np.max(meanwf)
  coll = ['firebrick', 'dodgerblue', 'darkgreen', 'orchid']

  xticks = np.arange(0, nsam+32, 32)
  for spgroup in tqdm(range(16), desc='Grouped by SP'):
    pagename = "SiPM Tile %02i\nSP %02i" % (tile, spgroup)

    fig = plt.figure(figsize=(8.27, 11.69-3.5))
    fig.suptitle(pagename,fontsize=14)

    ax = fig.add_subplot(1, 1, 1)

    ax.set_xlim(0, nsam)
    ax.set_ylim(min, max)
    ax.axhline(y=0, ls='--', color='grey', lw=0.5)
    ax.axhline(y=meanpeak, ls='--', color='grey', lw=0.5)
    [ax.axvline(x=x,ls=':', color='grey', lw=0.5) for x in xticks]

    wfsp = np.zeros(nsam)
    sp_max = -999
    for sp in range(4):
      tmpix = spgroup*4 + sp 
      campix = tile*64 + tmpix
      pix_max = np.max(wf[tmpix][40:80])
      if pix_max > sp_max: sp_max = pix_max
      wfsp += wf[tmpix]
    
    wfsp /= 4

    for sp in range(4):
      tmpix = spgroup*4 + sp 
      campix = tile*64 + tmpix
      pix_max = np.max(wf[tmpix][40:80]) 
      status = 'ok'
      if (pix_max < 0.8 * sp_max) and (pix_max > 0.55 * sp_max):
        status = '<0.8'
      elif pix_max <= 0.2 * sp_max:
        status = 'dead'   
      elif pix_max <= 0.55 * sp_max:
        status = '<0.55'

	
      ax.plot(wf[tmpix], lw=1, alpha=0.9, color=coll[sp], 
		label='Pix=%02i CamPix=%04i Status=%s' % (tmpix, campix, status))

    ax.plot(wfsp, color='black', lw=1, alpha=0.8, ls='--', label="SP Mean")
    #ax.text(0.05, 0.95, '%i' % spgroup, va='top', fontsize=6, transform=ax.transAxes)
    plt.xlabel('Time (ns)')
    plt.ylabel('Amplitude (ADC)')
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.xaxis.set_minor_locator(AutoMinorLocator(8))
    plt.legend(loc='upper right')

    pdf.savefig(fig)
    plt.close("all")



def plot_wf_sp(pdf, wf, pagename, tile):
  
  nsam = len(wf[0])
  meanwf = np.mean(wf, axis=0)
  min = np.min(np.min(wf))
  max = np.max(np.max(wf))*1.5
  meanpeak = np.max(meanwf)
  coll = ['firebrick', 'dodgerblue', 'darkgreen', 'orchid']
  
  fig = plt.figure(figsize=(8.27, 11.69-3.5))
  fig.suptitle(pagename,fontsize=14)
  plt.text(0.06, 0.5, "ADC", rotation=90, fontsize=10, transform=plt.gcf().transFigure)
  plt.text(0.5, 0.06, "Sample", fontsize=10, transform=plt.gcf().transFigure)
  plt.axis('off')

  xticks = np.arange(0, nsam+32, 32)
  for spgroup in tqdm(range(16), desc='Grouped by SP'):
    ax = fig.add_subplot(4, 4, spgroup+1)

    ax.set_xlim(0, nsam)
    ax.set_ylim(min, max)
    ax.axhline(y=0, ls='--', color='grey', lw=0.5)
    ax.axhline(y=meanpeak, ls='--', color='grey', lw=0.5)
    [ax.axvline(x=x,ls=':', color='grey', lw=0.5) for x in xticks]

    wfsp = np.zeros(nsam)
    sp_max = -999

    for sp in range(4):
      tmpix = spgroup*4 + sp 
      campix = tile*64 + tmpix
      pix_max = np.max(wf[tmpix][40:80])
      if pix_max > sp_max: sp_max = pix_max
      wfsp += (wf[tmpix])
    
    wfsp /= 4

    for sp in range(4):
      tmpix = spgroup*4 + sp 
      campix = tile*64 + tmpix
      pix_max = np.max(wf[tmpix][40:80]) 
      status = 'ok'
      if (pix_max < 0.8 * sp_max) and (pix_max > 0.55 * sp_max):
        status = '<0.8'
      elif pix_max <= 0.2 * sp_max:
        status = 'dead'
      elif pix_max <= 0.55 * sp_max:
        status = '<0.55'

	
      ax.plot(wf[tmpix], lw=1, alpha=0.9, color=coll[sp], 
		label='Pix=%02i CamPix=%04i Status=%s' % (tmpix, campix, status))

    #ax.plot(wfsp, color='black', lw=1, alpha=0.8, ls='--', label="SP Mean")
    ax.text(0.05, 0.95, '%i' % spgroup, va='top', fontsize=6, transform=ax.transAxes)
    plt.legend(loc='upper right')

    if spgroup % 4 == 0:
      ax.yaxis.set_minor_locator(AutoMinorLocator())
    else:
      plt.setp(ax.get_yticklabels(), visible=False)
      ax.yaxis.set_visible(False)

    if spgroup > 11:
      ax.xaxis.set_minor_locator(AutoMinorLocator(8))
      ax.set_xticks(xticks[:-1])
    else:
      plt.setp(ax.get_xticklabels(), visible=False)
      ax.xaxis.set_visible(False)
  
  fig.subplots_adjust(hspace=0.0, wspace=0.0)
  pdf.savefig(fig)
  plt.close("all")

'''
def plot_HV_groups(fname_r0, tile,avwf):

#Remove the average of the first 32 samples from the average wf of each pixel
  #print(avwf[0])

  #base = np.zeros((64,32))
  

  os.makedirs('Tile_%i' %(tile))
  j=0
  i=4
  k=1
  for k in range(16):
  
    for pix in range(j,i):

      plt.plot(avwf[pix], lw=1, alpha=0.8, label=('Camera Pixel %i' %(pix+(tile*64))))
      plt.ylim(ymin=400, ymax=np.max(avwf)+50)
    plt.legend()
    plt.xlabel('Time (ns)')
    plt.ylabel('Amplitude (ADC)')
    plt.savefig('./Tile_%i/Tile_%i_HV_group_%i' %(tile,tile,k)) 
    plt.close()

    j+=4
    i+=4
  k+=1

#add the pdf plotting stuff 
'''


def plot_res(fname_r0):
  r1 = TIOReader(fname_r0)
  nev = r1.n_events
  print ("Number of events in file = %i" % nev)
  avwf = np.zeros((64,r1.n_samples))
  for iev in range(nev):
     wf = r1[iev]
     avwf += wf
     
  avwf/=r1.n_events
  norm = np.max(np.mean(avwf, axis=0))
  print('norm',norm)
  plt.plot(np.mean(avwf, axis=0), color='grey', lw=2)
  plt.show()

  for pix, wf in enumerate(avwf):
       status = 'ok'
       amp = np.max(wf) / norm
       if amp < 0.6: 
          status = 'low'
       if amp > 1.4: 
          status = 'high'
       #asic =
       print('%i %0.2f %s' %(pix, amp, status))
       plt.plot(wf, lw=1, alpha=0.8)	
  plt.show()
  


def main():
    output_path = './'

    tm_ip = '192.168.12.122'
    my_ip = '192.168.12.1'

    description = 'Check for broken SiPM pixels'
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=Formatter)
    parser.add_argument('-o', '--out', dest='output_path', action='store', required=False, help='where to stick the results', default=output_path)
    parser.add_argument('-p', '--plot', dest='plot', action='store_true',required=False, help='dont just store results, plot as we go', default=True)
    parser.add_argument('-t', '--tile', dest='tile', action='store',required=True, help='Tile number (0-31)')

    parser.add_argument('-s', '--sn', dest='sn', action='store',required=True, help='Tile serial number')
    parser.add_argument('-a', '--acq', dest='acq', action='store_true',required=False, help='Take data', default=False)
    args = parser.parse_args()

    output_path = args.output_path
    plot = args.plot
    tile = int(args.tile)
    sn = int(args.sn)
    acq = args.acq

    # Make output file 

    fname_res ='%sSiPM%02i_SN%10i.results' % (output_path,tile,sn)
    fname_r0 = '%sSiPM%02i_SN%10i_r0.tio' % (output_path,tile,sn)
    fname_r0_2 = '%sSiPM%02i_SN%10i_ped_r0.tio' % (output_path,tile,sn)
    #print(fname_ped)
	
    if acq:
      if os.path.exists(fname_res):
         os.remove(fname_res)
      if os.path.exists(fname_r0):
         os.remove(fname_r0)
      if os.path.exists(fname_r0_2):
         os.remove(fname_r0_2)

      tm = setup_tm(my_ip, tm_ip, delay=310) #reduce delay to shift peak left in window
     # take_data(my_ip=my_ip, tm=tm, fname=fname_r0_2, hvon=False, sleep=2)
      take_data(my_ip=my_ip, tm=tm, fname=fname_r0, hvon=True, sleep=2)
      #subt_avwf = subtract_pedestal(avwf, fname_ped)

   # plot_res(fname_r0)
    avwf = make_avwf(fname_r0)
    savwf = np.zeros((64,len(avwf[0])))
    for i,wf in enumerate(avwf):
      savwf[i] = savitzky_golay(wf, 5, 2)
    #plot_HV_groups(fname_r0, tile,avwf)
    make_plots(savwf, tile, sn)

if __name__ == '__main__':
    main()
