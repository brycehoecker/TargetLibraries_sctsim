#small example for controlling the active 1:16 splitter
#written by Adrian Zink (adrian.zink@fau.de)

import serial
import time



def enableChannels(mask,device) : #enable the selected channels
  var = [100 , mask & 0xFF, (mask >> 8 & 0xFF)]
  device.write(var)
  time.sleep(1)
  print(device.read(1000))
  
def readVoltage(device) : #read ADCs, returns value in mV
  var = [101]
  device.write(var)
  time.sleep(1)
  print(device.read(1000))


if __name__ == "__main__" :
  ser0 = serial.Serial('/dev/ttyACM0', 9600, timeout=0) #check with dmesg which ttyACM/ttyUSB the arduino uses, or COM on windows
  ser1 = serial.Serial('/dev/ttyACM1', 9600, timeout=0)
  ser0.read(1000) #clean old readings, there might be some
  ser1.read(1000)
  #bitmask0 = 0b0000000000000000 #enable mask, channel 1 most left, need mapping if connected to mudule/buffer
  #bitmask1 = 0b0000000000000000
  bitmask0 = 0xffff #enable mask, channel 1 most left, need mapping if connected to mudule/buffer
  bitmask1 = 0xffff
  print("Channels 1-16")
  enableChannels(bitmask0,ser0)
  readVoltage(ser0)  
  print("Channels 17-32")
  enableChannels(bitmask1,ser1)
  readVoltage(ser1)
  
  exit()




