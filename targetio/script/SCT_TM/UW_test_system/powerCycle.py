#!/usr/bin/env/ python
import time
import BrickPowerSupply
#import logging

def powerCycle(stabelizationTime=10):
	bps = BrickPowerSupply.BrickPowerSupply('2200','/dev/tty.usbserial')
	time.sleep(0.5)
	bps.open()
	bps.outputOff()
	time.sleep(5)
	bps.outputOn()
	print("Wait", stabelizationTime, "seconds before connection to board.")
	#logging.info("Wait %d seconds before connection to board.", stabelizationTime)
	time.sleep(stabelizationTime)

	return bps

def powerOff(bps):
	bps.outputOff()

if __name__ == "__main__":
    bps = BrickPowerSupply.BrickPowerSupply('2200', '/dev/tty.usbserial')
    time.sleep(0.5)
    bps.open()
    time.sleep(2)
    bps.outputOff()
