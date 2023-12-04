import pexpect

# connect to pi, navigate to program and execute it
def executeConnection():
	ssh=pexpect.spawn('ssh pi@cta5')			#start ssh application
	ssh.expect('$')
	ssh.sendline("cd /home/pi/Desktop/BP_SPI_interface")    #navigate to directory
	ssh.expect('$')
	ssh.sendline("sudo ./bp_test_pi")			#execute program	
	ssh.expect('exit')					#last line of program prompt
	return ssh

def logout(ssh):
	ssh.sendline("x")
	ssh.sendline("logout")


# sends a sync signal
def sendSync(ssh):
	ssh.sendline("s")
	ssh.expect("exit")
	print ssh.before

#Get Hardware trigger count
def requestTrigCount(ssh):
	ssh.sendline("c")
	ssh.expect("HW")
	###print ssh.before
	dataOut = ssh.before
	lines = dataOut.strip().split(' ')
	return int(lines[-1])

def sendCalTrig(ssh):
	ssh.sendline("t")
	ssh.expect("Units")
	print ssh.before


def sendModTrig(ssh):
	ssh.sendline("k")
##	ssh.expect("exit")
	print ssh.before


# can find the hex values for the modules being turned on
def turnOnSlot(slotList):
	mask = 0b0	
	for slot in slotList:
		turnOn = (0b1<<slot)
		binCommand = (turnOn|mask)
		hexCommand = hex(binCommand)
		mask = binCommand
		print binCommand
		print hexCommand

# tell backplane which slots to deliver power to
# use hexadecimal number with on bits to specify the slots turned on
# hexSlots should be a string
def powerFEE(ssh, hexSlots):
	ssh.sendline("n")
	ssh.expect("FFFF:")
	print ssh.before
	ssh.sendline(hexSlots)
	ssh.expect("exit")
	print ssh.before

# sets trigger mask with file that closes all triggers (during setup)
def setTriggerMaskClosed(ssh, output=1):
	ssh.sendline("j")
	ssh.expect("read!")
	if(output):
		print ssh.before
	ssh.sendline("trigger_mask_null")
	ssh.expect("exit")
	if(output):
		print ssh.before


# sets trigger mask for data taking for single group
def setTriggerMaskSingle(ssh, module, asic, group, output=1):
	ssh.sendline("5")
	ssh.expect("triggering!")
	if(output):
		print ssh.before
	ssh.sendline(str(module))
	ssh.expect("triggering!")
	if(output):
		print ssh.before
	ssh.sendline(str(asic))
	ssh.expect("triggering!")
	if(output):
		print ssh.before
	ssh.sendline(str(group))
	ssh.expect("exit")
	if(output):
		print ssh.before

def getTimingInformation(ssh,output = 1):
	'''In progress function for testing the lack of nanosecond level precision
	This one is for getting the ns clock time'''
	ssh.sendline("c")
	ssh.expect("ns")
	clock_time = ssh.before.strip().split(' ')
	return int(clock_time[-1])

	

# sets trigger mask for data taking
def setTriggerMask(ssh, output=1):
	ssh.sendline("j")
	ssh.expect("read!")
	if(output):
		print ssh.before
	ssh.sendline("trigger_mask")
	ssh.expect("exit")
	if(output):
		print ssh.before

def enableTACK(ssh):
	ssh.sendline("g")
	ssh.expect("16-31")
	print ssh.before
	ssh.sendline("6f")
	ssh.expect("exit")
	print ssh.before

def disableTACK(ssh):
	ssh.sendline("g")
	ssh.expect("16-31")
	print ssh.before
	ssh.sendline("0")
	ssh.expect("exit")
	print ssh.before

def setHoldOff(ssh,holdTime):
	ssh.sendline("o")
	ssh.expect("hex :")
	print ssh.before
	ssh.sendline(holdTime)
	ssh.expect("exit")
	print ssh.before

if __name__ == "__main__":
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

