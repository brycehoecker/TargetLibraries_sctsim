from sct_toolkit import waveform

ped_number = 322343
ped_name = 'runFiles/pedestal_database_{}.h5'.format(ped_number)

run_number = 322344
modules = [118,125,126,119,108,121,110,128,123,124,112,100,111,114,107]
wf = waveform()
wf.write_events(run_number, modules, ped_name=ped_name, check_overwrite=False)
