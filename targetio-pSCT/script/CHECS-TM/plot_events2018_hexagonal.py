import target_driver
import target_io
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
import numpy as np
import pdb
import reportlab
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
#import plotly.plotly as py


filename_raw = "/media/cta/157bfe11-9587-4947-8a3e-1e814c5c25dc/Messungen_Stefan/Raw/file_0_r0.tio"
filename_cal = "/media/cta/157bfe11-9587-4947-8a3e-1e814c5c25dc/Messungen_Stefan/Raw/file_0_r1.tio"

Nsamples = 8*32
SCALE=13.6
OFFSET=700

plotchan = 0

reader_raw = target_io.EventFileReader(filename_raw)
reader_cal = target_io.EventFileReader(filename_cal)
NEvents  = reader_raw.GetNEvents()

print(NEvents, "events read")

ampl_raw = np.zeros([64,NEvents,Nsamples])
ampl_cal = np.zeros([64,NEvents,Nsamples])






#ax2[0].set_title("raw ADC counts",fontsize=10)
#ax2[1].set_title("pedestal substracted ADC counts", fontsize=10)

#ax_cal =plt.subplot(211)
#ax_cal.set_xlabel("sample",fontsize=14)
#ax_cal.set_ylabel("pedestal substracted ADC counts", fontsize=14)
#ax_cal.set_title("Channel "+str(channel))

nevt = 20

timestamp=0
timestamp_prev=0

if nevt==0:
    nevt=NEvents



for ievt in range(0,nevt,1):
	event_head = target_driver.EventHeader()
	ret=reader_raw.GetEventHeader(ievt,event_head)
	#get timestamp in ns from event header
	timestamp=event_head.GetTACK()
	print("\nEvent ",ievt, " Timestamp in ns",timestamp, " Time since last Event in us ",(timestamp-timestamp_prev)/1000.)
	timestamp_prev=timestamp
	#first get the right packet from event, if only one channel/packet, then packetnumber = channel
	for group in range (0,16):
	    rawdata_raw = reader_raw.GetEventPacket(ievt,int(group))
	    rawdata_cal = reader_cal.GetEventPacket(ievt,int(group))
	    packet_raw = target_driver.DataPacket()
	    packet_cal = target_driver.DataPacket()
	    packet_raw.Assign(rawdata_raw, reader_raw.GetPacketSize())
	    packet_cal.Assign(rawdata_cal, reader_cal.GetPacketSize())
	    if group == 0:
	    	print("Starting Block: Col",packet_raw.GetColumn(),"Row",packet_raw.GetColumn(),"Phase",packet_raw.GetBlockPhase())
	    for gchannel in range(0,4):
		    #get the waveform, if only one channel/packet, only one waveform!
		    wf_raw = packet_raw.GetWaveform(int(gchannel))
		    wf_cal = packet_cal.GetWaveform(int(gchannel))
		    ampl_raw[group*4+gchannel][ievt]=wf_raw.GetADCArray(Nsamples)
		    ampl_cal[group*4+gchannel][ievt]=((wf_cal.GetADC16bitArray(Nsamples))/SCALE)-OFFSET
   
        
    
	#ax2[0].plot(ampl_raw[plotchan][ievt],alpha=0.7)
	#ax2[1].plot(ampl_cal[plotchan][ievt],alpha=0.7)
	#ax2[0].set_xlim([0, 200])
	#ax2[1].set_ylim([-10, 10])
	#for i in range (0,64):
		#ax2[i%8,int(i/8)].set_xlim([0, 200])
		#ax2[i%8,int(i/8)].set_ylim([-10, 10])
		#ax2[i%8,int(i/8)].plot(ampl_cal[i][ievt],alpha=0.7)
		#alt



fig = plt.figure()
gs = gridspec.GridSpec(18, 18)

ax=[]

ax.append(plt.subplot2grid((18,18), (2,5), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (4,4), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (4,6), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (6,5), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (0,8), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (0,6), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (0,4), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (2,7), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (2,9), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (4,10), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (4,8), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (6,9), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (0,12), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (0,10), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (2,13), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (2,11), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (4,14), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (4,12), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (6,15), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (6,13), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (6,11), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (8,12), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (8,10), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (10,11), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (8,16), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (8,14), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (10,15), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (10,13), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (12,14), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (12,12), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (14,13), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (14,11), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (10,9), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (12,10), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (12,8), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (14,9), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (6,7), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (8,8), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (8,6), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (10,7), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (14,7), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (16,10), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (16,8), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (16,6), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (2,15), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (2,1), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (14,1), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (16,12), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (10,1), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (12,2), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (14,3), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (16,4), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (10,5), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (12,4), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (12,6), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (14,5), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (6,3), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (8,4), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (8,2), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (10,3), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (2,3), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (4,2), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (6,1), colspan=2, rowspan=2))
ax.append(plt.subplot2grid((18,18), (8,0), colspan=2, rowspan=2))

xulim = 200
xllim = 0
yulim = 50
yllim = -10

for channel in range (0,64):
    ax[channel].set_xlim([xllim, xulim])
    ax[channel].set_ylim([yllim, yulim])
    #plt.rc('font', size=6)
    #plt.rc('axes', titlesize=6)
    #plt.rc('axes', labelsize=6)
    #plt.rc('xtick', labelsize=6)
    #plt.rc('ytick', labelsize=6)
    for event in range (0,nevt):
        ax[channel].plot(ampl_cal[channel,event])
        
        #optional ELEC-Channel anzeigen
        ax[channel].text(xulim-70, yulim-25, channel, fontsize=10)
        
        #optional Achsen anzeigen
        ax[channel].axes.get_xaxis().set_visible(False)
        ax[channel].axes.get_yaxis().set_visible(False)

#SC1
linecolorSC1 = 'indigo'
facecolorSC1 = 'white'
for channel in range (0,4):
    ax[channel].set_facecolor(facecolorSC1)
    ax[channel].spines['left'].set_color(linecolorSC1)
    ax[channel].spines['right'].set_color(linecolorSC1)
    ax[channel].spines['bottom'].set_color(linecolorSC1)
    ax[channel].spines['top'].set_color(linecolorSC1)
#SC2
linecolorSC2 = 'darkcyan'
facecolorSC2 = 'white'
for channel in range (4,8):
    ax[channel].set_facecolor(facecolorSC2)
    ax[channel].spines['left'].set_color(linecolorSC2)
    ax[channel].spines['right'].set_color(linecolorSC2)
    ax[channel].spines['bottom'].set_color(linecolorSC2)
    ax[channel].spines['top'].set_color(linecolorSC2)
#SC3
linecolorSC3 = 'olivedrab'
facecolorSC3 = 'white'
for channel in range (8,12):
    ax[channel].set_facecolor(facecolorSC3)
    ax[channel].spines['left'].set_color(linecolorSC3)
    ax[channel].spines['right'].set_color(linecolorSC3)
    ax[channel].spines['bottom'].set_color(linecolorSC3)
    ax[channel].spines['top'].set_color(linecolorSC3)
#SC4
linecolorSC4 = 'indigo'
facecolorSC4 = 'white'
for channel in range (12,16):
    ax[channel].set_facecolor(facecolorSC4)
    ax[channel].spines['left'].set_color(linecolorSC4)
    ax[channel].spines['right'].set_color(linecolorSC4)
    ax[channel].spines['bottom'].set_color(linecolorSC4)
    ax[channel].spines['top'].set_color(linecolorSC4)
#SC5
linecolorSC5 = 'saddlebrown'
facecolorSC5 = 'white'
for channel in range (16,20):
    ax[channel].set_facecolor(facecolorSC5)
    ax[channel].spines['left'].set_color(linecolorSC5)
    ax[channel].spines['right'].set_color(linecolorSC5)
    ax[channel].spines['bottom'].set_color(linecolorSC5)
    ax[channel].spines['top'].set_color(linecolorSC5)
#SC6
linecolorSC6 = 'darkcyan'
facecolorSC6 = 'white'
for channel in range (20,24):
    ax[channel].set_facecolor(facecolorSC6)
    ax[channel].spines['left'].set_color(linecolorSC6)
    ax[channel].spines['right'].set_color(linecolorSC6)
    ax[channel].spines['bottom'].set_color(linecolorSC6)
    ax[channel].spines['top'].set_color(linecolorSC6)
#SC7
linecolorSC7 = 'indigo'
facecolorSC7 = 'white'
for channel in range (24,28):
    ax[channel].set_facecolor(facecolorSC7)
    ax[channel].spines['left'].set_color(linecolorSC7)
    ax[channel].spines['right'].set_color(linecolorSC7)
    ax[channel].spines['bottom'].set_color(linecolorSC7)
    ax[channel].spines['top'].set_color(linecolorSC7)
#SC8
linecolorSC8 = 'saddlebrown'
facecolorSC8 = 'white'
for channel in range (28,32):
    ax[channel].set_facecolor(facecolorSC8)
    ax[channel].spines['left'].set_color(linecolorSC8)
    ax[channel].spines['right'].set_color(linecolorSC8)
    ax[channel].spines['bottom'].set_color(linecolorSC8)
    ax[channel].spines['top'].set_color(linecolorSC8)
#SC9
linecolorSC9 = 'indigo'
facecolorSC9 = 'white'
for channel in range (32,36):
    ax[channel].set_facecolor(facecolorSC9)
    ax[channel].spines['left'].set_color(linecolorSC9)
    ax[channel].spines['right'].set_color(linecolorSC9)
    ax[channel].spines['bottom'].set_color(linecolorSC9)
    ax[channel].spines['top'].set_color(linecolorSC9)
#SC10
linecolorSC10 = 'saddlebrown'
facecolorSC10 = 'white'
for channel in range (36,40):
    ax[channel].set_facecolor(facecolorSC10)
    ax[channel].spines['left'].set_color(linecolorSC10)
    ax[channel].spines['right'].set_color(linecolorSC10)
    ax[channel].spines['bottom'].set_color(linecolorSC10)
    ax[channel].spines['top'].set_color(linecolorSC10)
#SC11
linecolorSC11 = 'darkcyan'
facecolorSC11 = 'white'
for channel in range (40,44):
    ax[channel].set_facecolor(facecolorSC11)
    ax[channel].spines['left'].set_color(linecolorSC11)
    ax[channel].spines['right'].set_color(linecolorSC11)
    ax[channel].spines['bottom'].set_color(linecolorSC11)
    ax[channel].spines['top'].set_color(linecolorSC11)
#SC12
linecolorSC12 = 'olivedrab'
facecolorSC12 = 'white'
for channel in range (44,48):
    ax[channel].set_facecolor(facecolorSC12)
    ax[channel].spines['left'].set_color(linecolorSC12)
    ax[channel].spines['right'].set_color(linecolorSC12)
    ax[channel].spines['bottom'].set_color(linecolorSC12)
    ax[channel].spines['top'].set_color(linecolorSC12)
#SC13
linecolorSC13 = 'indigo'
facecolorSC13 = 'white'
for channel in range (48,52):
    ax[channel].set_facecolor(facecolorSC13)
    ax[channel].spines['left'].set_color(linecolorSC13)
    ax[channel].spines['right'].set_color(linecolorSC13)
    ax[channel].spines['bottom'].set_color(linecolorSC13)
    ax[channel].spines['top'].set_color(linecolorSC13)
#SC14
linecolorSC14 = 'olivedrab'
facecolorSC14 = 'white'
for channel in range (52,56):
    ax[channel].set_facecolor(facecolorSC14)
    ax[channel].spines['left'].set_color(linecolorSC14)
    ax[channel].spines['right'].set_color(linecolorSC14)
    ax[channel].spines['bottom'].set_color(linecolorSC14)
    ax[channel].spines['top'].set_color(linecolorSC14)
#SC15
linecolorSC15 = 'darkcyan'
facecolorSC15 = 'white'
for channel in range (56,60):
    ax[channel].set_facecolor(facecolorSC15)
    ax[channel].spines['left'].set_color(linecolorSC15)
    ax[channel].spines['right'].set_color(linecolorSC15)
    ax[channel].spines['bottom'].set_color(linecolorSC15)
    ax[channel].spines['top'].set_color(linecolorSC15)
#SC16
linecolorSC16 = 'saddlebrown'
facecolorSC16 = 'white'
for channel in range (60,64):
    ax[channel].set_facecolor(facecolorSC16)
    ax[channel].spines['left'].set_color(linecolorSC16)
    ax[channel].spines['right'].set_color(linecolorSC16)
    ax[channel].spines['bottom'].set_color(linecolorSC16)
    ax[channel].spines['top'].set_color(linecolorSC16)

#gs.update(wspace=0.5, hspace=5)




plt.show()

 
c = canvas.Canvas("/media/cta/157bfe11-9587-4947-8a3e-1e814c5c25dc/Messungen_Stefan/Raw/channels.pdf")
c.setPageSize(landscape)
c.drawString(100,750,"Welcome to Reportlab!")
c.save()