import telnetlib
import time

tn = telnetlib.Telnet("172.16.55.150")

tn.write("VSET 24\n")
output = tn.read_until("V", 4)
vset = float(output.split(' ')[0])
print "This is the return:", output, vset


if(int(vset)==24):
	tn.write("PWR ON\n")
	output = tn.read_until("ON", 10)
	time.sleep(3)
	tn.write("VREAD\n")
	output = tn.read_until("V", 10)
	vread = float(output.split(' ')[0])
	if(int(vread)>=23):
		print "Powered Acopian successfully:", output
	time.sleep(30)
tn.write("PWR OFF\n")
tn.close()
