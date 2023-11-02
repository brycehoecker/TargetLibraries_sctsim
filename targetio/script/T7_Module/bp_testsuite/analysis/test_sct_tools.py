from sct_toolkit import pedestal, waveform
import matplotlib.pyplot as plt
import numpy as np

wf = waveform('runFiles/run322344.h5')
attrs = wf.get_attributes(verbose=True)


#example: plot calibrated waveforms in module 123, asic0, channel6
waveform = np.array(wf.get_branch('Module123/Asic0/Channel6/cal_waveform'))
plt.figure()
for samples in waveform:
    plt.plot(samples, linewidth=0.5)
plt.plot(np.mean(waveform,axis=0),'k',lw=2.)
plt.xlabel('Time (ns)')
plt.ylabel('ADC Counts')
plt.show()

#example: plot avg calibrated waveform in each module, asic, channel
plt.figure()
for Nmod in wf.get_module_list():
    for Nasic in wf.get_asic_list():
        for Nchannel in wf.get_channel_list():
            waveforms = np.array(wf.get_branch('Module{}/Asic{}/Channel{}/cal_waveform'.format(Nmod,Nasic,Nchannel)))
            avg_waveform = np.mean(waveforms,axis=0)
            #exclude dead channels
            if np.amax(avg_waveform) > 0.:
                plt.plot(avg_waveform)
plt.xlabel('Time (ns)')
plt.ylabel('ADC Counts')
plt.show()

