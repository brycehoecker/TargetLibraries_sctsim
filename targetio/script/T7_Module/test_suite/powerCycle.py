#!/usr/bin/env/ python
import time
import BrickPowerSupply
#import logging

def powerCycle(stabelizationTime=20):
	bps = BrickPowerSupply.BrickPowerSupply('2200','/dev/tty.usbserial')
	time.sleep(0.5)
	bps.open()
	bps.outputOff()
	time.sleep(5)
	bps.outputOn()
	print("Wait, %d, seconds before connection to board.", stabelizationTime)
	#logging.info("Wait %d seconds before connection to board.", stabelizationTime)
	time.sleep(stabelizationTime)

	return bps

def powerOff(bps):
	bps.outputOff()
