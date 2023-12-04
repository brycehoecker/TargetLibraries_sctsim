# Justin Vandenbroucke
# Created Mar 25 2016
# Power cycle the lab power supply (Keithley 2200) output, in order to power cycle the attached module.
# After powering off, monitor until current drops sufficiently close to zero (about 2 seconds).
# After powering on, monitor until current stabilizes high (about 10 seconds).

# Import modules
import sys, BrickPowerSupply, time

# Set up
psumodel = '2200'
psuname = '/dev/tty.usbserial'

def cycle():
	onCurrent = 0.663	# current above which we consider the system to be on
	offCurrent = 0.01	# current below which we consider system to be off
	mVPerV = 1000
	mAPerA = 1000
	bps = BrickPowerSupply.BrickPowerSupply(psumodel,psuname)
	bps.open()
	bps.setVoltage(12.0)
	bps.outputOff()
	print "Powered off.  Waiting until current drops below %d mA." % int(offCurrent*mAPerA)
	current = float(bps.keithley.readI())
	
	while current > offCurrent:
		current = float(bps.keithley.readI())
		voltage = float(bps.keithley.readV())
		print "Voltage = %.3f V.  Current = %.3f A." % (voltage,current)
		time.sleep(1)

	bps.outputOn()
	print "Powered on.  Will monitor current until it reaches at least %.3f A." % onCurrent
	current = float(bps.keithley.readI())
	while current < onCurrent:
		current = float(bps.keithley.readI())
		voltage = float(bps.keithley.readV())
		print "Voltage = %.3f V.  Current = %.3f A." % (voltage,current)
		time.sleep(1)
	bps.close()

if __name__ == "__main__":
	cycle()
