import pexpect
import time
# connect to pi, navigate to program and execute it
def executeConnection():
	ssh=pexpect.spawn('ssh pi@172.16.55.147', timeout=10)			#start ssh application
	#ssh.expect('$')
	#ssh.sendline("cd /home/pi/Desktop/BP_SPI_interface")    #navigate to directory
	#ssh.expect('$')
	#ssh.sendline("sudo ./bp_test_pi")			#execute program	
	#ssh.expect('exit')					#last line of program prompt
	return ssh








def logout(ssh):
	ssh.sendline("x")
	ssh.sendline("logout")




def setChannel(ssh, channel):
	ssh.sendline("sudo python mini-circuits-USB-1SP16T-83H.py 1 "+str(channel) )
	ssh.expect("done")
	print (ssh.before)


def getState(ssh):
	ssh.sendline("sudo python mini-circuits-USB-1SP16T-83H.py 0")
	ssh.expect("done")
	print(ssh.before)



# sends a sync signal
def sendSync(ssh):
	ssh.sendline("s")
	ssh.expect("exit")
	print (ssh.before)

#Get Hardware trigger count
def requestTrigCount(ssh):
	ssh.sendline("c")
	ssh.expect("HW")
	###print ssh.before
	dataOut = ssh.before
	lines = dataOut.strip().split(' ')
	return int(lines[-1])

def requestHitPattern(ssh):
	hitPattern = []
	ssh.sendline("7")
	ssh.expect("read:")
	for i in range(32):
		ssh.expect(",")
		dataOut = ssh.before
		lines = dataOut.strip().split(',')
		hitPattern.append(lines[0])
#	print hitPattern
	return hitPattern

def resetHitPattern(ssh):
	ssh.sendline("l")


def getTimingInformation(ssh):
	'''In progress function for testing the lack of nanosecond level precision
	This one is for getting the ns clock time'''
	ssh.sendline("c")
	ssh.expect(" ns")
	clock_time = ssh.before.strip().split(' ')
	return int(clock_time[-1])

def setTrigAtTime(ssh,des_time,until = 1):
	'''
	
	Args:
	ssh: duh
	until(int): time until the desired trigger, in ns
	'''
	if(until):
		current_time = getTimingInformation(ssh)
		trigger_time = current_time + des_time
	else:
		trigger_time = des_time
	trigger_time_hex = hex(trigger_time)[2:]
	trigger_time_hex = "0"*(16-len(trigger_time_hex))+trigger_time_hex
	ssh.sendline("d")
	ssh.expect("hex: ")
	#print trigger_time_hex[:4]
	ssh.sendline(trigger_time_hex[:4])
	ssh.expect("hex: ")
	#print trigger_time_hex[4:8]
	ssh.sendline(trigger_time_hex[4:8])
	ssh.expect("hex: ")				
	#print trigger_time_hex[8:12]
	ssh.sendline(trigger_time_hex[8:12])
	ssh.expect("hex: ")
	#print trigger_time_hex[12:16]
	ssh.sendline(trigger_time_hex[12:16])
	print ("The times: ", current_time, trigger_time, hex(trigger_time))

	#do something afterwards? No, that will be in brendan_DataGathering.py
	return trigger_time		
	

def sendCalTrig(ssh,runDuration,freq):
	ssh.sendline("t")
	ssh.expect("seconds!")
	print(ssh.before, "seconds!")
	ssh.sendline(str(runDuration))
	ssh.expect("Hz!")
	print(ssh.before, "Hz!")
	ssh.sendline(str(freq))
	print("setting cal trig freq to {}".format(freq))


def sendModTrig(ssh,runDuration,freq):
	ssh.sendline("k")
	#ssh.expect("seconds!")
	#print ssh.before, "seconds!"
	#ssh.sendline(str(runDuration))
	#ssh.expect("Hz!")
	print(ssh.before, "exit")
	#ssh.sendline(str(freq))
	ssh.expect("exit")
	#print "setting mod trig freq to {}".format(freq)


# can find the hex values for the modules being turned on
def turnOnSlot(slotList):
	mask = 0b0	
	for slot in slotList:
		turnOn = (0b1<<slot)
		binCommand = (turnOn|mask)
		hexCommand = hex(binCommand)
		mask = binCommand
		print(binCommand)
		print(hexCommand)

# tell backplane which slots to deliver power to
# use hexadecimal number with on bits to specify the slots turned on
# hexSlots should be a string
def powerFEE(ssh, hexSlots):
	ssh.sendline("n")
	ssh.expect("FFFF:")
	print(ssh.before)
	ssh.sendline(hexSlots)
	ssh.expect("exit")
	print(ssh.before)

# sets trigger mask with file that closes all triggers (during setup)
def setTriggerMaskClosed(ssh, output=1):
	ssh.sendline("j")
	ssh.expect("read!")
	if(output):
		print(ssh.before)
	ssh.sendline("trigger_mask_null")
	ssh.expect("exit")
	if(output):
		print(ssh.before)


# sets trigger mask for data taking for single group
def setTriggerMaskSingle(ssh, module, asic, group, output=1):
	ssh.sendline("5")
	ssh.expect("triggering!")
	if(output):
		print(ssh.before)
	ssh.sendline(str(module))
	ssh.expect("triggering!")
	if(output):
		print(ssh.before)
	ssh.sendline(str(asic))
	ssh.expect("triggering!")
	if(output):
		print(ssh.before)
	ssh.sendline(str(group))
	ssh.expect("exit")
	if(output):
		print(ssh.before)



# sets trigger mask for data taking
def setTriggerMask(ssh, output=1):
	ssh.sendline("j")
	ssh.expect("read!")
	if(output):
		print(ssh.before)
	ssh.sendline("trigger_mask")
	ssh.expect("exit")
	if(output):
		print(ssh.before)

def enableTACK(ssh):
	ssh.sendline("g")
	ssh.expect("16-31")
	print(ssh.before)
	ssh.sendline("6f")
	ssh.expect("exit")
	print(ssh.before)

def disableTACK(ssh):
	ssh.sendline("g")
	ssh.expect("16-31")
	print(ssh.before)
	ssh.sendline("0")
	ssh.expect("exit")
	print(ssh.before)

def setHoldOff(ssh,holdTime):
	ssh.sendline("o")
	ssh.expect("hex :")
	print(ssh.before)
	ssh.sendline(holdTime)
	ssh.expect("exit")
	print(ssh.before)

if __name__ == "__main__":
	ssh = executeConnection()
	time.sleep(1)	
	setChannel(ssh,2)
	time.sleep(5)	
	#getState(ssh)
	#time.sleep(5)	
	#channel = 2

	setChannel(ssh,0)
	#ssh.sendline("sudo python mini-circuits-USB-1SP16T-83H.py 1 "+str(channel) )

	
	#pattern = requestHitPattern(ssh)
	#print pattern, len(pattern)
	"""
	#start ssh application
	ssh=pexpect.spawn('ssh pi@cta1')
	ssh.expect('$')						#find command prompt
	ssh.sendline("cd /home/pi/Desktop/BP_SPI_interface")	#navigate to directory
	ssh.expect('$')
	ssh.sendline("sudo ./bp_test_pi")			#execute program	
	ssh.expect('exit')					#last line of program prompt

	#sync command
	ssh.sendline("s")					

	"""
