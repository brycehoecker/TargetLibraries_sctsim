import piCom
import time


pi = piCom.executeConnection()
piCom.powerFEE(pi, "0")
time.sleep(5)

for i in range(10000):
	piCom.sendCalTrig(pi)
	time.sleep(0.2)	
