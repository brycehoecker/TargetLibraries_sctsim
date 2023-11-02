import time

import base_222

def main():
    input("Module on")
    test = base_222.FEETest("vped_tf_by_hand")
    test.set_vped()
    test.set_vtrim()
    test.set_comm_params(trigger_delay=800)
    test.set_pmtref4_from_file()
    with open("vped_asic0_ch0_tf_data.txt") as f:
        f.write("DAC,mV\n")
        for vped in range(0, 4095, 500):
            test.set_single_vped(0, 0, Vped=int(vped))
            time.sleep(0.5)
            data = int(input(f"DAC: {vped}\nmV: "))
            f.write(f"{vped},{data}\n")

if __name__ == "__main__":
    main()