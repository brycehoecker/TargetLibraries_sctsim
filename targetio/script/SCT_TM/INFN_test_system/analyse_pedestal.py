#!/usr/bin/env python
#from __future__ import division
import target_driver
import target_io
import matplotlib.pyplot as plt
import numpy as np
#import pdb
import os
import argparse
import matplotlib.mlab as mlab
from cell_id_map import pedestal
from scipy import stats
from MyLogging import logger

dpi=100


parser = argparse.ArgumentParser()
parser.add_argument("-f", "--filename", help="Name of input file", type=str, default="pedestal.fits")
parser.add_argument("-D","--directory", help="Directory where output files will be saved", type=str, default="./")
parser.add_argument("-N" ,"--Nevents", help="Number of events to be displayed. 0 will show all events in the file", type=int, default="0")
parser.add_argument("-c" ,"--channel", help="Channel to be displayed", type=int, default="0")
parser.add_argument("-n" ,"--Nchannels", help="Number of channels to be analysed", type=int, default=1)
parser.add_argument("-t" ,"--tag", help="tag to append to output file name", type=str, default="")
parser.add_argument("-b" ,"--numblocks", help="number of Blocks of 32 samples", type=int, default=14)
#parser.add_argument("-i" ,"--info", help="infos about run", type=str, default="")
args = parser.parse_args()

outdir = args.directory+'/'
plotdir = outdir+"plots/"
os.system("mkdir -p "+plotdir)
#info_ped = args.info

filename=args.directory+'/'+args.filename
minchannel=args.channel
maxchannel=args.channel+args.Nchannels
Nsamples = args.numblocks*32
channel=args.channel

reader = target_io.EventFileReader(filename)
n  = reader.GetNEvents()
logger.info(str(n)+" events read")

Nevents = args.Nevents
if Nevents <= 0 or Nevents > n:
    Nevents = n

totalcells = 1 << 12 #14
#totalcells+=256
number_of_capacitors=1<<12 #14
#number_of_capacitors+=256
capacitors = np.arange(number_of_capacitors) # array 0,1, ... 16383

Nplot = min(Nevents, 300)

cell_ids_list = []
data_list = np.zeros( (64,Nevents, Nsamples) )

ped_values = np.zeros( (64,number_of_capacitors) )
sigma_capacitors =  np.zeros( (64,number_of_capacitors) )
sample_count_list = np.zeros( (64,number_of_capacitors) ) 
global_average_list = np.zeros( 64 ) 
global_sigma_list = np.zeros(64)
ped = pedestal(Nsamples) ## to map correct cells

amplitude = np.zeros((64,Nevents,Nsamples))
firstsample = np.zeros(Nevents).astype(int)

### Read events
for ievt in range(Nevents):
    if ievt%1000==0:
        logger.info("Reading event " + str(ievt))
    for group in range (0,16):
        rawdata = reader.GetEventPacket(ievt,int(group))
        packet = target_driver.DataPacket()
        packet.Assign(rawdata, reader.GetPacketSize())
        if group == 0:
            firstsample[ievt]=(packet.GetRow())*32+(packet.GetColumn())*8*32+(packet.GetBlockPhase())
            firstcell = packet.GetFirstCellId()
            block_id = int(firstcell / 32)
            phase_block = firstcell % 32
            #logger.info("ievt: {}, firstample: {}, firstcell: {}, block_id: {}, phase_block: {}".format(ievt,firstsample[ievt],firstcell, block_id, phase_block))
            #input()

        for gchannel in range(0,4):
            wf = packet.GetWaveform(int(gchannel))
            #amplitude[group*4+gchannel][ievt]=wf.GetADCArray(Nsamples)
            data_list[group*4+gchannel][ievt]=wf.GetADCArray(Nsamples)

logger.info(str(firstsample))
logger.info(str(firstsample.max()) + " "+ str(firstsample.min()))
#exit()
            
############################
## Raw buffer scan (all events)
############################

for channel in range(minchannel, maxchannel):
  logger.info("Reading channel " + str(channel))
  average = np.zeros(number_of_capacitors)
  squares = np.zeros(number_of_capacitors)
  sigma_capacitors1 = np.zeros(number_of_capacitors)
  sample_count = np.zeros(number_of_capacitors)
  y = np.zeros(Nsamples)
  x = np.zeros(Nsamples)

#  plt.figure()
#  plt.clf()
#  ax = plt.subplot(111)
#  ax.set_xlabel("capacitor",fontsize=14)
#  ax.set_ylabel("raw ADC counts", fontsize=14)
#  ax.set_title("All events before pedestal correction - channel %i \n%i events, %i samples each - %s" % (channel, Nevents, Nsamples, args.tag))
#  ax.set_xlim(0,totalcells)
#  ax.set_ylim(0, 1 << 12)

  for ievt in range(Nevents):
    #rawdata = reader.GetEventPacket(ievt,channel)#second entry is asic/channel, only one enabled in this case
    #packet = target_driver.DataPacket()
    #packet.Assign(rawdata, reader.GetPacketSize())
    #firstcell = packet.GetFirstCellId()
    firstcell = firstsample[ievt]
    block_id = int(firstcell / 32)
    phase_block = firstcell % 32
    cell_ids = ped.get_cell_ids(block_id,phase_block)
    if firstcell>2000:
        #logger.info(str(firstcell)+ " " + str(cell_ids))
        #input()
        pass
    #cell_ids = (np.arange(Nsamples) + firstcell) % totalcells   ### OLD
    #wf = packet.GetWaveform(0)

    #for i in range(Nsamples):
    #    #x[i] = buf_idx
    #    y[i] = wf.GetADC(i)
    y = data_list[channel,ievt]
    cell_ids_list.append(cell_ids[:])
    #data_list[channel][ievt]=y[:]
    
    average[cell_ids] += y
    squares[cell_ids] += y**2
    sample_count[cell_ids] += 1.
    if firstcell>2000:
        #logger.info(str(firstcell) + " " + str(cell_ids) + " "  + str(cell_ids_list[-1]) + " " + str(average[cell_ids]) + " " + str(sample_count[cell_ids]))
        #input()
        pass
 
    #for i in range(Nsamples):
    #    buf_idx = (i + firstcell) % totalcells
    #    x[i] = buf_idx
    #    y[i] = wf.GetADC(i)
    #    average[buf_idx] += wf.GetADC(i)
    #    sample_count[buf_idx] += 1.



  #for i in range(number_of_capacitors):
  #  if sample_count[i] == 0:
  #    average[i] = 0
  #  else:
  #    average[i] /= sample_count[i]

  average = np.where(sample_count>0, average/sample_count, 0) 
  sigma_capacitors1 = np.where(sample_count>0, (squares/sample_count-average**2)**0.5, 0) 
  global_average = average.mean()
  global_sigma = average.std()
  ped_values[channel] = average
  sigma_capacitors[channel] = sigma_capacitors1
  sample_count_list[channel] = sample_count
  global_average_list[channel] = global_average
  global_sigma_list[channel] = global_sigma

  #global_average = 0
  #for i in range(number_of_capacitors):
  #  global_average += average[i]
  #global_average /= number_of_capacitors
  
  #text_file = open("pedestal_channel%i.txt" % (channel), "w")
  #for i in range(totalcells):
  #  text_file.write("%f\n" % average[i])

  txt_file = outdir+ "pedestal_channel_%i.txt" %channel
  np.savetxt(txt_file, ped_values[channel])


############################
## Raw buffer plot (all events)
############################
fig = plt.figure()
fig.set_size_inches(18.5, 12.5, forward=True)

logger.info("Plotting raw events...")
for channel in range(minchannel, maxchannel):
  #plt.figure()

  plt.clf()
  ax = plt.subplot(111)
  ax.set_xlabel("capacitor",fontsize=14)
  ax.set_ylabel("raw ADC counts", fontsize=14)
  ax.set_title("All events before pedestal correction - channel %i \n%i events, %i samples each - %s" % (channel, Nevents, Nsamples, args.tag))
  ax.set_xlim(0,totalcells)
  ax.set_ylim(0, 1 << 12)

  for c_ids, y in zip(cell_ids_list[:Nplot], data_list[channel][:Nplot]):
  #for c_ids, y in zip(cell_ids_list[::100], data_list[channel][::100]):
      ax.plot(c_ids, y, '-')#, markersize=10)
  plt.savefig(plotdir+ "1_bufferscan_raw_channel%i_%s.png" % (channel, args.tag), dpi=dpi)

#exit()
############################
## Pedestal corrected buffer scan (all events)
############################
nspikes_list=[]
for channel in range(minchannel, maxchannel):
  logger.info("Plotting channel " + str(channel))
  #plt.figure()
  plt.clf()


  ax = plt.subplot(111)
  ax.set_xlabel("capacitor",fontsize=14)
  ax.set_ylabel("ADC counts (pedestal subtracted)", fontsize=14)
  ax.set_title("All events after pedestal correction - channel %i (global average re-added!)\n%i events, %i samples each - %s" % (channel, Nevents, Nsamples, args.tag))
  ax.set_xlim(0,totalcells)
  #ax.set_ylim(0, 1<<12)
  ax.set_ylim(global_average_list[channel]-500.,global_average_list[channel]+500.)

  for c_ids, y in zip(cell_ids_list[:Nplot], data_list[channel][:Nplot]):
  #for c_ids, y in zip(cell_ids_list[::100], data_list[channel][::100]):
      y1 = (y- ped_values[channel][c_ids])+global_average_list[channel]
      ax.plot(c_ids, y1, '-')

  plt.savefig(plotdir+ "2_bufferscan_pedsub_channel%i_%s.png" % (channel, args.tag), dpi=dpi)

  '''
  for ievt in range(Nevents):
    rawdata = reader.GetEventPacket(ievt,channel)#second entry is asic/channel, only one enabled in this case
    packet = target_driver.DataPacket()
    packet.Assign(rawdata, reader.GetPacketSize())
    firstcell = packet.GetFirstCellId()
    wf = packet.GetWaveform(0)


    for i in range(Nsamples):
        buf_idx = (firstcell + i) % totalcells
        x[i] = buf_idx 
        y[i] = wf.GetADC(i) + global_average
    
    
    for i in range(Nsamples):
      y[i] -= average[buf_idx]


    if (firstcell + (Nsamples -1) >= totalcells):
      diff = totalcells - firstcell
      ax.plot(x[0:diff], y[0:diff], alpha=0.7)
      ax.plot(x[diff:Nsamples], y[diff:Nsamples], alpha=0.7)
    else:
      ax.plot(x, y, alpha=0.7)
  plt.savefig("2_bufferscan_pedsub_channel%i_%s.png" % (channel, args.tag))
  '''


############################
## Pedestal and pedestal sigma
############################    

  ## get spikes
  #nspikes = len(np.where(np.logical_or(ped_values[channel] < global_average_list[channel]-10*global_sigma_list[channel], ped_values[channel] > global_average_list[channel]+10*global_sigma_list[channel] ))[0])
  mask = np.zeros(totalcells).astype(bool)
  mask[range(31, totalcells, 32)]= True
  a,b,r,p,e = stats.linregress(np.arange(totalcells)[mask], ped_values[channel][mask])
  delta_ped = ped_values[channel][mask] - (a*np.arange(totalcells)[mask]+b)
  err = ( ( (delta_ped )**2 ).sum()/( mask.sum()-2) )**0.5
  nspikes = len(np.where(np.logical_or( delta_ped < -5*err, delta_ped > 5*err))[0])

  mask1 = np.logical_not(mask)
  a1,b1,r,p,e = stats.linregress(np.arange(totalcells)[mask1], ped_values[channel][mask1])
  delta_ped = ped_values[channel][mask1] - (a1*np.arange(totalcells)[mask1]+b1)
  err1 = ( ( (delta_ped )**2 ).sum()/( mask1.sum()-2) )**0.5
  nspikes += len(np.where(np.logical_or( delta_ped < -5*err1, delta_ped > 5*err1))[0])
  
  #display a,a1,b,b1,err, err1
  nspikes_list.append(nspikes)
  #plt.figure()

  plt.clf()
  ax = plt.subplot(111)
  ax.set_title("Pedestal channel " + str(channel) + " - " + str(args.tag))
  
  #ax.set_xlim(0,totalcells)
  #ax.set_xlim(8192,8192+256)
  #ax.set_ylim(0, 1 << 12)

  #ax.set_xlabel("capacitor",fontsize=14)
  #ax.set_ylabel("average (raw ADC counts)", fontsize=14)
  ax.plot(capacitors[mask], ped_values[channel][mask], 'm')
  ax.plot(capacitors[mask1], ped_values[channel][mask1], 'b')
  ax.plot(capacitors, a*np.arange(totalcells)+b, 'r-')
  ax.plot(capacitors, a*np.arange(totalcells)+b+5*err, 'r--')
  ax.plot(capacitors, a*np.arange(totalcells)+b-5*err, 'r--')
  ax.plot(capacitors, a1*np.arange(totalcells)+b1, 'g-')
  ax.plot(capacitors, a1*np.arange(totalcells)+b1+5*err1, 'g--')
  ax.plot(capacitors, a1*np.arange(totalcells)+b1-5*err1, 'g--')
  ax.set_xlabel("capacitor",fontsize=14)
  ax.set_ylabel("ADC counts", fontsize=14)

  plt.savefig(plotdir+ "4_pedestal_ch%i_%s.png" % (channel, args.tag), dpi=dpi)
  #plt.show()


  plt.clf()
  ax = plt.subplot(111)
  ax.set_title("Pedestal sigma channel " + str(channel) + " - " + str(args.tag))
  
  #ax.set_xlim(0,totalcells)
  #ax.set_xlim(8192,8192+256)
  #ax.set_ylim(0, 1 << 12)

  #ax.set_xlabel("capacitor",fontsize=14)
  #ax.set_ylabel("average (raw ADC counts)", fontsize=14)
  ax.plot(capacitors[mask],  sigma_capacitors[channel][mask], 'm')
  ax.plot(capacitors[mask1],  sigma_capacitors[channel][mask1], 'b')
  ax.set_xlabel("capacitor",fontsize=14)
  ax.set_ylabel("ADC counts", fontsize=14)

  plt.savefig(plotdir+ "5_pedestal_sigma_ch%i_%s.png" % (channel, args.tag), dpi=dpi)


############################
## Number of samples
############################    
  #plt.figure()

  plt.clf()
  ax = plt.subplot(111)
  ax.set_title("Number of samples for pedestal calculation")
  
  #ax.set_xlim(8192,8192+256)
  ax.set_xlabel("capacitor",fontsize=14)
  ax.set_ylabel("number of samples", fontsize=14)
  ax.plot(capacitors, sample_count_list[channel])
  plt.savefig(plotdir+ "6_number_of_samples_ch%i_%s.png" % (channel, args.tag), dpi=dpi)

############################
## Raw -- auto Y       
############################
'''
for channel in range(minchannel, maxchannel):
  plt.clf()
  ax = plt.subplot(111)
  ax.set_xlabel("capacitor",fontsize=14)
  ax.set_ylabel("raw ADC counts", fontsize=14)
  ax.set_title("All events before pedestal correction - channel %i (autoscale Y)\n%i events, %i samples each - %s" % (channel, Nevents, Nsamples, args.tag))
  ax.set_xlim(0,totalcells)
  for ievt in range(Nevents):
    rawdata = reader.GetEventPacket(ievt,channel)#second entry is asic/channel, only one enabled in this case
    packet = target_driver.DataPacket()
    packet.Assign(rawdata, reader.GetPacketSize())
    firstcell = packet.GetFirstCellId()
    wf = packet.GetWaveform(0)
    for i in range(Nsamples):
        buf_idx = (i + firstcell) % totalcells
        x[i] = buf_idx
        y[i] = wf.GetADC(i)
    if (firstcell + (Nsamples -1) >= totalcells):
        diff = totalcells - firstcell
        ax.plot(x[0:diff], y[0:diff], alpha=0.7)
        ax.plot(x[diff:Nsamples], y[diff:Nsamples], alpha=0.7)
    else:
        ax.plot(x, y, alpha=0.7)
  plt.savefig("6_bufferscan_raw_autoY_channel%i_%s.png" % (channel, args.tag))



############################
## Pedestal corrected buffer scan (all events) - auto Y 
############################


for channel in range(minchannel, maxchannel):
  plt.clf()

  ax = plt.subplot(111)
  ax.set_xlabel("capacitor",fontsize=14)
  ax.set_ylabel("ADC counts (pedestal subtracted)", fontsize=14)
  ax.set_title("All events after pedestal correction - channel %i (autoscale Y)\n%i events, %i samples each - %s" % (channel, Nevents, Nsamples, args.tag))
  ax.set_xlim(0,totalcells)
  for ievt in range(Nevents):
    rawdata = reader.GetEventPacket(ievt,channel)#second entry is asic/channel, only one enabled in this case
    packet = target_driver.DataPacket()
    packet.Assign(rawdata, reader.GetPacketSize())
    firstcell = packet.GetFirstCellId()
    wf = packet.GetWaveform(0)





    for i in range(Nsamples):
        buf_idx = (firstcell + i) % totalcells
        x[i] = buf_idx
        y[i] = wf.GetADC(i) - average[buf_idx]



    if (firstcell + (Nsamples -1) >= totalcells):
      diff = totalcells - firstcell
      ax.plot(x[0:diff], y[0:diff], alpha=0.7)
      ax.plot(x[diff:Nsamples], y[diff:Nsamples], alpha=0.7)
    else:
      ax.plot(x, y, alpha=0.7)


  plt.savefig("7_bufferscan_pedsub_autoY_channel%i_%s.png" % (channel, args.tag))
############################
## Example events
############################

if Nevents >= 2010:
 for ievt in range(2000,2010):
  for channel in range(minchannel, maxchannel):
    plt.clf()
    ax = plt.subplot(111)
    ax.set_title("Example event: event %i, channel %i (after pedestal subtraction)\n%s" % (ievt, channel, args.tag))
    ax.set_xlabel("sample",fontsize=14)
    ax.set_ylabel("ADC counts (pedestal subtracted)", fontsize=14)
    ax.set_xlim(0,Nsamples)
    major_ticks = np.arange(0, Nsamples+1, 32)
    minor_ticks = np.arange(0, Nsamples+1, 8)
    ax.set_xticks(major_ticks)
    ax.set_xticks(minor_ticks, minor=True)

    rawdata = reader.GetEventPacket(ievt,channel)#second entry is asic/channel, only one enabled in this case
    packet = target_driver.DataPacket()
    packet.Assign(rawdata, reader.GetPacketSize())
    firstcell = packet.GetFirstCellId()
    wf = packet.GetWaveform(0)
    



    for i in range(Nsamples):
        buf_idx = (firstcell + i) % totalcells
        x[i] = i
        y[i] = wf.GetADC(i) - average[buf_idx]

    #ax.plot(x, y, alpha=0.7)

    if (firstcell + (Nsamples -1) >= totalcells):
      diff = totalcells - firstcell
      ax.plot(x[0:diff], y[0:diff], alpha=0.7)
      ax.plot(x[diff:Nsamples], y[diff:Nsamples], alpha=0.7)
    else:
      ax.plot(x, y, alpha=0.7)
 


    plt.text(0.0, 0.0, "FirstCellId = "+str(firstcell), fontsize=15,  horizontalalignment='left', verticalalignment='bottom',transform = ax.transAxes)
    plt.savefig("example_event%i_channel%i_ped_subtracted_%s.png" % (ievt, channel, args.tag))

'''


############################
## Noise distribution
############################

ped_file = open(outdir+ "results_pedestal.txt","w")
#ped_file.write('#'+info_ped+'\n')
ped_file.write('#Channel\tTarget_Nr\tSubchannel\tped_av\tsigma\tglobal_sigma\tNspikes\tAvgSamples\n')


logger.info("Plotting noise distribution...")

all_sigma=[]
for channel in range(minchannel, maxchannel):
  #plt.figure()
  data=[]
  totalentries=0
  plt.clf()
  ax = plt.subplot(111)

  for c_ids, y in zip(cell_ids_list, data_list[channel]):
      y1 = y- ped_values[channel][c_ids]
      data.extend(y1)

  totalentries = len(data)
  data = np.array(data)
  ax.set_title("Noise distribution after pedestal correction \nChannel%i - %s" % (channel, args.tag))
  ax.set_xlabel("ADC counts",fontsize=14)
  xlims = (-40,40)
  ax.set_xlim(xlims[0], xlims[1])
  ax.set_ylabel("counts", fontsize=14)
  n, bins, patches = plt.hist(data, 200, range=xlims, normed=0, facecolor='green', alpha=0.75)
  uflow = (data<xlims[0]).sum()
  oflow = (data>xlims[1]).sum()
  mean = np.mean(data) #[np.logical_and(data>-10,data<10)])
  variance = np.var(data) #[np.logical_and(data>-10,data<10)])
  sigma = np.sqrt(variance)
  all_sigma.append(sigma)
  x = np.linspace(xlims[0], xlims[1], 500)
  #plt.plot(x, mlab.normpdf(x, mean, sigma))
  y =  mlab.normpdf(x, mean, sigma)* sum(n * np.diff(bins))
  plt.plot(x, y, 'r')
  mystr = 'mean = %.2f ADC counts\nsigma = %.2f ADC counts\nFWHM = 2.355*sigma = %.2f ADC counts' % (mean, sigma, 2.355*sigma)
  message= "Nsamples = "+str(Nsamples) + "\nNevents = "+str(Nevents) + "\ntotalEntries = " + str(totalentries)+ "\nUnderflow = " + str(uflow)+ "\nOverflow = " + str(oflow)
  plt.text(0.01, 0.01, message, fontsize=15,  horizontalalignment='left', verticalalignment='bottom',transform = ax.transAxes)
  plt.text(0.01, 0.99, mystr, fontsize=13, horizontalalignment='left', verticalalignment='top', transform=ax.transAxes)
  #plt.yscale('log')
  #plt.ylim(0.9,None)
  plt.savefig(plotdir+ "3_noise_distribution_channel%i_%s.png" % (channel, args.tag), dpi=dpi)


  sample_count_avg = sample_count_list[channel].mean()

  ped_file.write(str(channel)+'\t'+str(channel/16+1)+'\t'+ str(channel%16)+'\t'+str(global_average_list[channel])+'\t'+ str(sigma)+'\t'+str(global_sigma_list[channel])+'\t'+str(nspikes_list[channel])+'\t'+str(sample_count_avg)+'\n')

ped_file.close()
#plt.show()

plt.figure()
plt.hist(all_sigma)
plt.show()
