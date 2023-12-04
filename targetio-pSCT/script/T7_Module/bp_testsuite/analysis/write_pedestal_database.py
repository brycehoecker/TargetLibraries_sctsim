from sct_toolkit import pedestal

run_number = 322343
ped_name = '/home/ctauser/runFiles/pedestal_database_{}.h5'.format(run_number)

#define list of module numbers (must be same order as when data was taken)
modules = [118,125,126,119,108,121,110,128,123,124,112,100,111,114,107]
ped = pedestal()
ped.make_pedestal_database(ped_name, run_number, modules, check_overwrite=True)
