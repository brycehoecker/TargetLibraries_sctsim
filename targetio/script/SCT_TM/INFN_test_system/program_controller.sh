cta-avrprog -q --target_host=192.168.12.173 -p 328 -U flash:w:peltier/PeltierFirmware_AVR_ATmega328_atmega328p_v4_2020-08-05.hex
## unlock some opcodes
#peltcmd --target_host="192.168.12.173" -w 37 1
## read peltier coefficient
#peltcmd --target_host="192.168.12.173" 97 0
## change peltier coefficient
#peltcmd --target_host="192.168.12.173" -w 97 1074266112

