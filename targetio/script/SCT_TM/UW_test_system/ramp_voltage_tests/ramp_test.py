import time

import base_222
import run_incr


def log_ramp_run(run, ramp, ramp_asic, ped):
    with open("ramp_log.txt", "a") as f:
        f.write(f"{run},{ramp},{ramp_asic},{ped}\n")


def take_ramp_data_run(ramp, ramp_asic, ped, thresh=1500, datadir=None):
    test = base_222.FEETest("ramp_test")
    test.set_vped()
    test.set_single_vped(ramp_asic, 0, Vped=ped)
    test.set_vtrim()
    test.set_comm_params(trigger_delay=800)
    test.set_pmtref4_from_file()
    run = int(run_incr.incr_run_number())
    if datadir:
        filename = f"{datadir}/run{run}.fits"
    else:
        filename = f"run{run}.fits"
    test.take_ramp_run(ramp,
                       ramp_asic,
                       filename=filename,
                       tack_enable_trig=0xffff,
                       thresh=thresh)
    log_ramp_run(run, ramp, ramp_asic, ped)
    time.sleep(1)


def test_data_taking():
    test = base_222.FEETest("ramp_test")
    test.set_vped()
    test.set_vtrim()
    test.set_comm_params(trigger_delay=600)
    test.set_pmtref4_from_file()
    test.start_data_taking(ext_trig_dir=0x0,
                           tack_enable_trig=0xffff,
                           thresh=1500)
    test.data_taking(duration=5)
    test.stop_data_taking()
    time.sleep(1)


def take_ped_ramp_data(ramp):
    test = base_222.FEETest("ramp_test")
    test.set_vped()
    test.set_vtrim()
    test.set_comm_params(trigger_delay=800)
    test.set_pmt_ref4_from_file()
    test.start_data_taking(ext_trig_dir=0x0,
                           tack_enable_trig=0xffff,
                           thresh=1000)
    test.data_taking(duration=15)
    test.stop_data_taking()
    time.sleep(1)


if __name__ == "__main__":
    input("Module on")
    input("Pulse on")
    datadir = "/Volumes/pSCT Lab Data"
    try:
        for ped in range(1200, 1500, 25)[::-1]:
            thresh = 1000
            take_ramp_data_run(2300, 0, ped, thresh=thresh, datadir=datadir)
    except Exception as ex:
        print(ex)
    input("Pulse off")
    input("Module off")
