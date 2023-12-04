from sct_toolkit import pedestal, waveform
import matplotlib.pyplot as plt
import numpy as np

runID = 322344
filename = "/home/ctauser/runFiles/run{}.h5".format(runID)

wf = waveform(filename)
attrs = wf.get_attributes(verbose=True)

modList=[118,125,126,119,108,121,110,128,123,124,112,100,111,114,107]
asic = 3
ch = 2

plt.figure()
for mod in modList:
	waveform = np.array(wf.get_branch('Module{}/Asic{}/Channel{}/cal_waveform'.format(mod,asic,ch)))
	plt.plot(np.mean(waveform,axis=0),lw=0.5)
	if mod==108:
		print np.mean(waveform,axis=0)[0]

plt.xlabel('Time (ns)')
plt.ylabel('ADC Counts')
plt.title('Waveforms for Asic {} Ch {}'.format(asic,ch))
plt.show()
