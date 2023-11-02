from sct_toolkit import pedestal, waveform
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec

runID = 322344
filename = "/home/ctauser/runFiles/run{}.h5".format(runID)

wf = waveform(filename)
attrs = wf.get_attributes(verbose=True)

modList=[118,125,126,119,108,121,110,128,123,124,112,100,111,114,107]
asic = 0
ch = 4

plt.figure()
for asic in range(4):
	fig = plt.figure('ASIC {}'.format(asic), (22.,10.))
	fig.suptitle("ASIC {}".format(asic), fontsize=16, fontweight='bold', bbox={'boxstyle':'round4','facecolor':'gray', 'alpha':0.5})
	gs = gridspec.GridSpec(4,4)
	gs.update(left=0.06,right= 0.98, top=0.93, bottom = 0.05, wspace=0.25,hspace=0.25)
	
	for ch in range(16):
		for mod in modList:
			ax = plt.subplot(gs[ch/4, ch%4])
			ax.set_xlabel('ns')
			ax.set_ylabel('raw ADC counts')
			ax.grid(True)
			plt.text(0.65, 0.9," Channel {}".format(ch), transform = ax.transAxes, bbox={'boxstyle':'roundtooth','facecolor':'grey', 'alpha':0.2})
			
			waveform = np.array(wf.get_branch('Module{}/Asic{}/Channel{}/cal_waveform'.format(mod,asic,ch)))
			if not (mod==108 and asic==3 and ch==2):
				plt.plot(np.mean(waveform,axis=0),lw=0.5)

	fig.savefig('/home/ctauser/Pictures/wf_overlays/run{}_asic{}_overlays'.format(runID, asic))
"""
plt.xlabel('Time (ns)')
plt.ylabel('ADC Counts')
plt.title('Waveforms for Asic {} Ch {}'.format(asic,ch))
"""
#plt.show()
