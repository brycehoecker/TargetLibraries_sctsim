import target_driver
import target_io
import time
#from astropy.io import ascii
import os
import sys
import run_control
import random
import datetime
import numpy as np
#Wisconsin specific modules:
import Keithley2200
import Keithley2000
import Agilent33600A
import piCom

hardsyncTrig_ena=0
externalTrig_ena=0
internalTrig_ena=0
temperatureTest_ena=0
crossTalk_ena=0
rateTest_ena=0
pedestal_ena=0
HV_test_ena=0
triggerDelay_ena=1
bps = Keithley2200.Keithley2200()
bps.powerModuleOn()

time.sleep(10)

homedir = os.environ['HOME']
td_directory = homedir + '/pSCT_module_control/svn_folder/CCC/TargetDriver/branches/issue37423/config'

timestamp = time.time()
dataset = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M')
#baseDir = dataset+'/'
baseDir = "{}/target5and7data/testData2019/module3/TARGETCTesting/".format(homedir)+dataset+'/'
try:
		os.mkdir(baseDir)
		os.chmod(baseDir, 0o777)
except:
		print "directory", baseDir, "already exists."

def Efficiency(module, trig_eff_duration):
    module.WriteSetting("TriggerEff_Duration", trig_eff_duration)
    ret, done_bit = module.ReadSetting("TriggerEff_DoneBit")
    time.sleep(0.1)
    while done_bit == 0:
        ret, done_bit = module.ReadSetting("TriggerEff_DoneBit")
    ret, N = module.ReadSetting("TriggEffCounter")
    return N - 1


hostname = run_control.getHostName()
outdirname = run_control.getDataDirname(hostname)
"""
runID = run_control.incrementRunNumber(outdirname)
print("Run ID: {}".format(runID))
outfile = "%srun%d.fits" % (outdirname, runID)
"""
my_ip = "192.168.12.1"
module_ip = "192.168.12.173"
initialize = True

module_def = "/Users/tmeures/svn_folder/CCC/TargetDriver/branches/issue37423/config/SCT_MSA_FPGA_Firmware0xC0000004.def"
asic_def = "/Users/tmeures/TargetDriverTrunk/config/TC_ASIC.def"
trigger_asic_def = "/Users/tmeures/TargetDriverTrunk/config/T5TEA_ASIC.def"

module_def = "{}/SCT_MSA_FPGA_Firmware0xC0000002.def".format(td_directory)
asic_def = '{}/pSCT_module_control/svn_folder/CCC/TargetDriver/trunk/config/TC_ASIC.def'.format(homedir)
trigger_asic_def = '{}/pSCT_module_control/svn_folder/CCC/TargetDriver/trunk/config/T5TEA_ASIC.def'.format(homedir)

module = target_driver.TargetModule(module_def, asic_def, trigger_asic_def, 0)
if initialize:
    module.EstablishSlowControlLink(my_ip, module_ip)
    module.Initialise()
    module.EnableDLLFeedback()
    print ("module initialized")
else:
    module.ReconnectToServer(my_ip, 8201, module_ip, 8105)

ret, fw = module.ReadRegister(0)
module.WriteSetting("TACK_EnableTrigger", 0)
#module.WriteSetting("HV_enable", 1)
print ("Firmware version: {:x}".format(fw))

#module.DisableHVAll()#disable all for safety, atm turn on by default

### Setting VPEDs ###
#with open(VPED_FILE) as f:
#  content = f.readlines()
#content = [x.strip() for x in content]
#print("Setting VPEDs to")
for asic in range(4):
  module.WriteTriggerASICSetting("VpedBias", asic, 1800, True)
  for channel in range(16):
    #print(str(asic) + "   " + str(channel) + "   " + str(asic*16+channel) + "   " + str(content[asic*16+channel]))
    module.WriteTriggerASICSetting("Vped_{}".format(channel), asic, 1200 ,True)#int(content[asic*16+channel]), True)
time.sleep(1)

### Setting optimized SSToutFB & VtrimT ###
#data = ascii.read(VTRIM_FILE)
#print(data)
for asics in range(4):
  #print("Setting SSToutFB_Delay of Asic " + str(asics) + " to " + str(int(data[asics][2])))
  module.WriteASICSetting("SSToutFB_Delay", asics, 58,True,False)#int(data[asics][2]), True, False) # standard value: 58
  #print("Setting VtrimT of Asic " + str(asics) + " to " + str(int(data[asics+4][2])))
  module.WriteASICSetting("VtrimT", asics, 1240,True,False)#int(data[asics+4][2]), True, False) # standard value: 1240
time.sleep(1)

for asic in range(4):
    module.WriteSetting("EnableChannelsASIC{}".format(asic), 0xffff)
#module.WriteSetting("Zero_Enable", 0x1)
module.WriteSetting("DoneSignalSpeedUp",0)
nblocks = 8
module.WriteSetting("NumberOfBlocks", nblocks-1)
module.WriteSetting("MaxChannelsInPacket", 4)

module.WriteSetting("TriggerDelay", 600) # lookback time between instant when the trigger is issued and the portion of the ASIC storage to digitize
module.WriteSetting("TACK_TriggerType", 0x0)
module.WriteSetting("TACK_TriggerMode", 0x0)

module.WriteTriggerASICSetting("Wbias_0", 0, 985, False)
module.WriteTriggerASICSetting("Wbias_1", 0, 985, False)
module.WriteTriggerASICSetting("Wbias_2", 0, 985, False)
module.WriteTriggerASICSetting("Wbias_3", 0, 985, False)

filename = "{}/target5and7data/testData2019/module3/T5TEATesting/PMTref4_levels.txt".format(homedir)
dat = np.loadtxt(filename)
for l in range(4):
	print dat[l*4,0]
	module.WriteTriggerASICSetting("PMTref4_0", int(dat[l*4,0]), int(dat[l*4,2]), True)
	module.WriteTriggerASICSetting("PMTref4_1", int(dat[l*4,0]), int(dat[l*4+1,2]), True)
	module.WriteTriggerASICSetting("PMTref4_2", int(dat[l*4,0]), int(dat[l*4+2,2]), True)
	module.WriteTriggerASICSetting("PMTref4_3", int(dat[l*4,0]), int(dat[l*4+3,2]), True)

module.WriteTriggerASICSetting("Thresh_0", 0,0, False)
module.WriteTriggerASICSetting("Thresh_1", 0,0, False)
module.WriteTriggerASICSetting("Thresh_2", 0,0, False)
module.WriteTriggerASICSetting("Thresh_3", 0,0, False)

module.WriteTriggerASICSetting("TTbias_A", 0,0x443, False)
module.WriteSetting("SR_DisableTrigger",0x1)

### let module head up a bit ###
#module.WriteSetting("ExtTriggerDirection", 0x1) # hardsync
#module.WriteSetting("TACK_EnableTrigger", 0x10000)

kNPacketsPerEvent = 16
# by default we have a data packet for each channel, this can be changed
kPacketSize = target_driver.DataPacket_CalculatePacketSizeInBytes(4, 32 * (nblocks))
kBufferDepth = 10000

#To avoid stray uncontrolled triggers:
module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers


if(hardsyncTrig_ena):


	for i in range(15):
		runID = run_control.incrementRunNumber(outdirname)
		print("Run ID: {}".format(runID))
		runName = "run"+str(runID)
	    	outfile = baseDir + runName + "hardsync_Vped_scan_{}.tio".format(int(1200+i*100))

	    	for asic in range(4):
			module.WriteTriggerASICSetting("VpedBias", asic, 1800, True)
		for channel in range(16):
		    #print(str(asic) + "   " + str(channel) + "   " + str(asic*16+channel) + "   " + str(content[asic*16+channel]))
		    module.WriteTriggerASICSetting("Vped_{}".format(channel), asic, 1200+i*100 ,True)#int(content[asic*16+channel]), True)
		######### Read Temperatures #############
		#print("\n------ Took data for {}s -------".format(i*5))
		#ret,temp =  module.GetTempI2CPrimary()
		#print ("Temperature Pri: ",temp)
		#ret, temp =  module.GetTempI2CAux()
		#print ("Temperature Aux: ",temp)
		time.sleep(0.2)

		listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
		listener.AddDAQListener(my_ip)
		listener.StartListening()
		writer = target_io.EventFileWriter(outfile, kNPacketsPerEvent, kPacketSize)
		buf = listener.GetEventBuffer()
		writer.StartWatchingBuffer(buf)

		####start data taking

		module.WriteSetting("ExtTriggerDirection", 0x1) # hardsync
		module.WriteSetting("TACK_EnableTrigger", 0x10000)  # hardware trigger
		time.sleep(0.2)
		module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers

		time.sleep(1)

		writer.StopWatchingBuffer()  # stops data storing in file

		buf.Flush()
		writer.Close()
		listener.StopListening()

if(externalTrig_ena):
	for asic in range(4):
		module.WriteTriggerASICSetting("VpedBias", asic, 1800, True)
		for channel in range(16):
		    #print(str(asic) + "   " + str(channel) + "   " + str(asic*16+channel) + "   " + str(content[asic*16+channel]))
		    module.WriteTriggerASICSetting("Vped_{}".format(channel), asic, 1200 ,True)#int(content[asic*16+channel]), True)
		######### Read Temperatures #############
	asic=3
	raw_input("Is the module powered ON?")
	ssh = piCom.executeConnection()
	time.sleep(2)
	for channel in range(8,16):
		for ampl in range(5):
			amplitude = (20 + 100*ampl)*1.0/1000.0
			runID = run_control.incrementRunNumber(outdirname)
			print("Run ID: {}".format(runID))
			runName = "run"+str(runID)
			outfile = baseDir + runName + "extTest_ampl{}_asic{}_channel{}.tio".format(int(amplitude*1000.0),asic,channel)

			listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
			listener.AddDAQListener(my_ip)
			listener.StartListening()
			writer = target_io.EventFileWriter(outfile, kNPacketsPerEvent, kPacketSize)
			buf = listener.GetEventBuffer()
			writer.StartWatchingBuffer(buf)

			####start data taking

			piCom.setChannel(ssh,channel+1)
			time.sleep(3)



			module.WriteSetting("ExtTriggerDirection", 0x0) # external trigger input


			fg = Agilent33600A.Agilent33600A()
			if(amplitude<1.0):
				fg.apply_pulse(100, amplitude, 0,5)
			else:
				print("Input pulse to strong")
			#fg.send_cmd("PULS:WIDTH 5e-9")
			time.sleep(1)


			fg.apply_trigger_pulse(100, 2.5, 0,500)

			module.WriteSetting("TACK_EnableTrigger", 0x10000)  # hardware trigger

			time.sleep(2)

			module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers


			fg.send_cmd("OUTPut2 OFF")
			time.sleep(1)
			fg.send_cmd("OUTPut1 OFF")


			time.sleep(1)

			####close connection to module and output file
			writer.StopWatchingBuffer()  # stops data storing in file

			buf.Flush()
			writer.Close()


	piCom.setChannel(ssh,0)



if(internalTrig_ena):

	fg = Agilent33600A.Agilent33600A()
	ssh = piCom.executeConnection()
	time.sleep(5)

	asic = 3
	#values = [1720,1810,1600,2000]
	values = [1600,1600,1600,1600]
	runCount=0
	for channel in range(0,16):
		piCom.setChannel(ssh,channel+1)
		time.sleep(5)
		for ampl in range(8):
			runCount+=1
			amplitude = 40 + 200*ampl
			amplitude = 2000 + 200*ampl
			group = int(asic*4 + channel/4)
			setting = 0x1 << group

			#values = np.loadtxt("/Users/tmeures/target5and7data/testData2019/module3/T5TEATesting/fixedTrigger.txt")
			thresh =int(values[group%4])  # int(values[group%4,2])
			print "Running channel:", channel, "the used threshold is:", thresh, "With amplitude:", amplitude
			print "The dataset is:", dataset
			runID = runCount  #run_control.incrementRunNumber(outdirname)
			print("Run ID: {}".format(runID))
			runName = "run"+str(runID)

			outfile=baseDir+'/'+runName+'internalTrigTest_group_'+str(group)+'_channel_'+str(channel)+'_ampl_'+str(amplitude)+'.tio'
			tempFile = baseDir + runName + "extTest_temperature.log"
			tf = open(tempFile,'w')
			print "Writing Threshodl for group", group%4, "on asic", group/4
			thresh_name='Thresh_'+str(int(group%4))
			module.WriteTriggerASICSetting(thresh_name,int(group/4),thresh, True)
			module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers

			listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
			listener.AddDAQListener(my_ip)
			listener.StartListening()
			writer = target_io.EventFileWriter(outfile, kNPacketsPerEvent, kPacketSize)
			buf = listener.GetEventBuffer()
			writer.StartWatchingBuffer(buf)

			####start data taking


			print "The input amplitude is:", amplitude/1000.0
			fg.apply_pulse(1000, amplitude/1000.0, 0,10)
			time.sleep(1)
			module.WriteSetting("TACK_EnableTrigger", setting)  # enable relevant trigger.

			time.sleep(1)

			module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers

			fg.send_cmd("OUTPut1 OFF")
			ret, temp =  module.GetTempI2CAux()
			currentTime = time.time()
			tf.write("%d    %f    \n" % (currentTime, temp) )

			time.sleep(1)
			tf.close()
			####close connection to module and output file
			writer.StopWatchingBuffer()  # stops data storing in file

			buf.Flush()
			writer.Close()


	piCom.setChannel(ssh,0)




if(crossTalk_ena):
	for asic in range(4):
		module.WriteTriggerASICSetting("VpedBias", asic, 1800, True)
		for channel in range(16):
		    #print(str(asic) + "   " + str(channel) + "   " + str(asic*16+channel) + "   " + str(content[asic*16+channel]))
		    module.WriteTriggerASICSetting("Vped_{}".format(channel), asic, 1200 ,True)#int(content[asic*16+channel]), True)
		######### Read Temperatures #############
	asic=0
	#raw_input("Is the module powered ON?")
	ssh = piCom.executeConnection()
	time.sleep(2)
	for channel in range(0,16):
			amplitude = 2000/1000.0
			runID = run_control.incrementRunNumber(outdirname)
			print("Run ID: {}".format(runID))
			runName = "run"+str(runID)
			outfile = baseDir + runName+ "crossTalkTest_ampl{}_asic{}_channel{}.tio".format(int(amplitude*1000.0),asic,channel)

			listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
			listener.AddDAQListener(my_ip)
			listener.StartListening()
			writer = target_io.EventFileWriter(outfile, kNPacketsPerEvent, kPacketSize)
			buf = listener.GetEventBuffer()
			writer.StartWatchingBuffer(buf)

			####start data taking

			piCom.setChannel(ssh,channel+1)
			time.sleep(5)



			module.WriteSetting("ExtTriggerDirection", 0x0) # external trigger input


			fg = Agilent33600A.Agilent33600A()
			if(amplitude<2.0):
				fg.apply_pulse(100, amplitude, 0,5)
			else:
				print("Input pulse to strong")
			#fg.send_cmd("PULS:WIDTH 5e-9")
			time.sleep(1)


			fg.apply_trigger_pulse(100, 2.5, 0,500)

			module.WriteSetting("TACK_EnableTrigger", 0x10000)  # hardware trigger

			time.sleep(2)

			module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers


			fg.send_cmd("OUTPut2 OFF")
			time.sleep(1)
			fg.send_cmd("OUTPut1 OFF")


			time.sleep(1)

			####close connection to module and output file
			writer.StopWatchingBuffer()  # stops data storing in file

			buf.Flush()
			writer.Close()


	piCom.setChannel(ssh,0)



if(rateTest_ena):

	nblocks = 4
	module.WriteSetting("NumberOfBlocks", nblocks-1)
	module.WriteSetting("MaxChannelsInPacket", 8)
	kNPacketsPerEvent = 8
	# by default we have a data packet for each channel, this can be changed
	kPacketSize = target_driver.DataPacket_CalculatePacketSizeInBytes(8, 32 * (nblocks))
	kBufferDepth = 10000

	fg = Agilent33600A.Agilent33600A()
	ssh = piCom.executeConnection()
	time.sleep(3)

	asic = 3
	#values = [1720,1810,1600,2000]
	values = [1750,1750,1750,1750]
	"""
	for channel in range(0,1):
		piCom.setChannel(ssh,channel+1)
		time.sleep(3)
		for freq in range(5):
			amplitude = 60
			group = int(asic*4 + channel/4)
			setting = 0x1 << group

			#values = np.loadtxt("/Users/tmeures/target5and7data/testData2019/module3/T5TEATesting/fixedTrigger.txt")
			thresh =int(values[group%4])  # int(values[group%4,2])
			print "the used threshold is:", thresh
			frequency = 2500 + freq*500

			outfile=baseDir+'/rateScanTest_group_'+str(group)+'_channel_'+str(channel)+'_freq_'+str(frequency)+'.tio'
			print "Writing Threshodl for group", group%4, "on asic", group/4
			thresh_name='Thresh_'+str(int(group%4))
			module.WriteTriggerASICSetting(thresh_name,int(group/4),thresh, True)

			listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
			listener.AddDAQListener(my_ip)
			listener.StartListening()
			writer = target_io.EventFileWriter(outfile, kNPacketsPerEvent, kPacketSize)
			buf = listener.GetEventBuffer()
			writer.StartWatchingBuffer(buf)

			####start data taking


			fg.apply_pulse(frequency, amplitude/1000.0, 0,5)
			time.sleep(1)
			module.WriteSetting("TACK_EnableTrigger", setting)  # enable relevant trigger.

			time.sleep(3)

			module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers

			fg.send_cmd("OUTPut1 OFF")

			time.sleep(1)

			####close connection to module and output file
			writer.StopWatchingBuffer()  # stops data storing in file

			buf.Flush()
			writer.Close()


	piCom.setChannel(ssh,0)
	"""
	asic = 3
	#values = [1720,1810,1600,2000]
	values = [1750,1750,1750,1750]
	tempEvents=0
	for channel in range(0,1):
		piCom.setChannel(ssh,channel+1)
		time.sleep(3)
		for th in range(20):
			amplitude = 60
			group = int(asic*4 + channel/4)

			#values = np.loadtxt("/Users/tmeures/target5and7data/testData2019/module3/T5TEATesting/fixedTrigger.txt")
			thresh = int( 1535 + th*1 ) #int(values[group%4])  # int(values[group%4,2])
			print "the used threshold is:", thresh

			runID = run_control.incrementRunNumber(outdirname)
			print("Run ID: {}".format(runID))
			runName = "run"+str(runID)
			outfile=baseDir+'/' +runName+ 'rateScanTest_group_'+str(group)+'_channel_'+str(channel)+'_thresh_'+str(thresh)+'.tio'
			print "Writing Threshodl for group", group%4, "on asic", group/4
			thresh_name='Thresh_'+str(int(group%4))
			module.WriteTriggerASICSetting(thresh_name,int(group/4),thresh, True)

			listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
			listener.AddDAQListener(my_ip)
			listener.StartListening()
			writer = target_io.EventFileWriter(outfile, kNPacketsPerEvent, kPacketSize)
			buf = listener.GetEventBuffer()
			writer.StartWatchingBuffer(buf)

			####start data taking


			frequency = 100
			#fg.apply_pulse(frequency, amplitude/1000.0, 0,5)
			ampl = 0.08
			fg.apply_noise(ampl,0)
			#fg.apply_pulse(500,0.02,0,10)
    			#module.WriteSetting("TriggerEff_Enable", 2**group)
			nEvents = module.ReadSetting("CountTACKsReceived")
			startTack = nEvents[1] & 0xffff
			start=time.time()
			setting = 2**group
			time.sleep(3)
			module.WriteSetting("TACK_EnableTrigger", setting)  # enable relevant trigger.
			#trigger_duration = 0.2
			#trig_eff_duration = int(trigger_duration / 8. * 1e9)
			#for i in range(2):
			time.sleep(5)
			#ret, temp =  module.GetTempI2CAux()
			#nEvents = module.ReadSetting("CountTACKsReceived")
			#counts=Efficiency(module,trig_eff_duration)
			#if(nEvents>tempEvents):
			#print( "Number of events:", counts, "           Rate:", dataRate, "Temperature Aux: ",temp)
				#else:
				#	print( "Number of events:", nEvents[1]-tempEvents+65535, "           Rate:", (nEvents[1]-tempEvents+65535), "temperature Aux: ", temp)

			module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers
			stop = time.time()
			nEvents = module.ReadSetting("CountTACKsReceived")
			stopTack = nEvents[1] & 0xffff
			print("elapsed time is:", stop-start, ". TACK count is:", stopTack - startTack)
			dataRate = buf.GetNumberToBeRead()

			fg.send_cmd("OUTPut1 OFF")

			time.sleep(1)

			####close connection to module and output file
			writer.StopWatchingBuffer()  # stops data storing in file

			buf.Flush()
			writer.Close()


	piCom.setChannel(ssh,0)
	fg.close()

if(pedestal_ena):
	for asic in range(4):
		module.WriteTriggerASICSetting("VpedBias", asic, 1800, True)
	for vped in range(2400,4100,100):	
		for channel in range(16):
			    #print(str(asic) + "   " + str(channel) + "   " + str(asic*16+channel) + "   " + str(content[asic*16+channel]))
			    module.WriteTriggerASICSetting("Vped_{}".format(channel), 0, vped ,False)#int(content[asic*16+channel]), True)
			######### Read Temperatures #############
		#raw_input("Is the module powered ON?")
		#ssh = piCom.executeConnection()
		#time.sleep(2)
		#for channel in range(8,16):
		#	for ampl in range(5):
		#		amplitude = (20 + 100*ampl)*1.0/1000.0
		runID = run_control.incrementRunNumber(outdirname)
		print("Run ID: {}".format(runID))
		runName = "run"+str(runID)
		outfile = baseDir + runName + "extTest_pedestal_"+str(vped)+"_.tio"
		tempFile = baseDir + runName + "extTest_temperature.log"

		listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
		listener.AddDAQListener(my_ip)
		listener.StartListening()
		writer = target_io.EventFileWriter(outfile, kNPacketsPerEvent, kPacketSize)
		buf = listener.GetEventBuffer()
		writer.StartWatchingBuffer(buf)

		####start data taking

		#piCom.setChannel(ssh,channel+1)
		#time.sleep(3)



		module.WriteSetting("ExtTriggerDirection", 0x0) # external trigger input


		fg = Agilent33600A.Agilent33600A()
		#if(amplitude<1.0):
		#	fg.apply_pulse(100, amplitude, 0,5)
		#else:
		#	print("Input pulse to strong")
		#fg.send_cmd("PULS:WIDTH 5e-9")
		time.sleep(0.2)


		fg.apply_trigger_pulse(2000, 2.5, 0,500)
		tf = open(tempFile,'w')
		startTime = time.time()
		module.WriteSetting("TACK_EnableTrigger", 0x10000)  # hardware trigger
		for i in range(10):
			ret, temp =  module.GetTempI2CAux()
			currentTime = time.time() - startTime
			tf.write("%d    %f    \n" % (currentTime, temp) )
			print ("Temperature Aux: ",temp)
			time.sleep(1)

		module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers
		tf.close()

		fg.send_cmd("OUTPut2 OFF")
		#time.sleep(1)
		#fg.send_cmd("OUTPut1 OFF")


		time.sleep(0.2)

		####close connection to module and output file
		writer.StopWatchingBuffer()  # stops data storing in file

		buf.Flush()
		writer.Close()


		#piCom.setChannel(ssh,0)

if(temperatureTest_ena):

	#fg = Agilent33600A.Agilent33600A()
	#ssh = piCom.executeConnection()
	#time.sleep(5)

	asic = 0
	#values = [1720,1810,1600,2000]
	values = [1750,1750,1750,1750]
	for channel in range(0,16):
		#piCom.setChannel(ssh,channel+1)
		#time.sleep(3)
		for count in range(1):
			amplitude = 200 + 200
			group = int(asic*4 + channel/4)
			setting = 0x1 << group

			#values = np.loadtxt("/Users/tmeures/target5and7data/testData2019/module3/T5TEATesting/fixedTrigger.txt")
			thresh =int(values[group%4])  # int(values[group%4,2])
			print("Running channel: {}\nthe used threshold is: {}\nWith amplitude: 20 mV".format(channel, thresh))#amplitude
			print("The dataset is: {}".format(dataset))
			runID = run_control.incrementRunNumber(outdirname)
			print("Run ID: {}".format(runID))
			runName = "run"+str(runID)

			outfile=baseDir+'/'+runName+'internalTrigTest_group_'+str(group)+'_channel_'+str(channel)+'_ampl_'+str(amplitude)+'.tio'
			tempFile = baseDir + runName + "extTest_temperature.log"
			print("Writing Threshold for group {} on asic {}".format(group%4, group/4))
			thresh_name='Thresh_'+str(int(group%4))
			module.WriteTriggerASICSetting(thresh_name,int(group/4),thresh, True)
			module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers

			tf = open(tempFile,'w')
			listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
			listener.AddDAQListener(my_ip)
			listener.StartListening()
			writer = target_io.EventFileWriter(outfile, kNPacketsPerEvent, kPacketSize)
			buf = listener.GetEventBuffer()
			writer.StartWatchingBuffer(buf)

			####start data taking


			print("The input amplitude is: {}".format(amplitude/1000.0))
			#fg.apply_pulse(500, amplitude/1000.0, 0,10)
			time.sleep(1)
			start = time.time()
			module.WriteSetting("TACK_EnableTrigger", setting)  # enable relevant trigger.

			time.sleep(2)
			ret, temp =  module.GetTempI2CAux()

			module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers
			currentTime = time.time()

			tf.write("%d    %f    \n" % (currentTime, temp) )
			print ("Temperature Aux: {}".format(temp))
			print("Elapsed time is:", currentTime - start)
			#fg.send_cmd("OUTPut1 OFF")

			time.sleep(1)
			tf.close()
			####close connection to module and output file
			writer.StopWatchingBuffer()  # stops data storing in file

			buf.Flush()
			writer.Close()


	#piCom.setChannel(ssh,0)
#module.WriteSetting("HV_enable", 0)

if(HV_test_ena):

	multimeter = Keithley2000.Keithley2000()
	multimeter.configure(readMode='voltage')

	module.WriteSetting("HV_enable", 1)

	time.sleep(1)
	raw_input("Set load.")
	voltage=0
	for i in range(5):
		multimeter.read()
		voltage+=multimeter.voltage/5.0
		time.sleep(1)
	
	ret, current = module.ReadHVCurrentInput()
	
	ret, HV_volts = module.ReadHVVoltageInput()
	
	print("The input current is:", current, ". The input voltage is:", HV_volts, "The output voltage is:", voltage)

	module.WriteSetting("HV_enable",0)


if(triggerDelay_ena):

	#fg = Agilent33600A.Agilent33600A()
	#ssh = piCom.executeConnection()
	#time.sleep(5)
	nblocks = 4
	module.WriteSetting("NumberOfBlocks", nblocks-1)
	module.WriteSetting("MaxChannelsInPacket", 8)
	kNPacketsPerEvent = 8
	# by default we have a data packet for each channel, this can be changed
	kPacketSize = target_driver.DataPacket_CalculatePacketSizeInBytes(8, 32 * (nblocks))
	kBufferDepth = 10000

	asic = 1
	#values = [1720,1810,1600,2000]
	values = [1000,1000,1000,1820]
	runCount=0
	for channel in range(12,13):
		#piCom.setChannel(ssh,channel+1)
		#time.sleep(5)
		for delay in range(70):
			trigDelay = 8024 + 64*delay
			module.WriteSetting("TriggerDelay", trigDelay) # lookback time between instant when the trigger is issued and the portion of the ASIC storage to digitize
			runCount+=1
			amplitude = 40
			group = int(asic*4 + channel/4)
			setting = 0x1 << group

			#values = np.loadtxt("/Users/tmeures/target5and7data/testData2019/module3/T5TEATesting/fixedTrigger.txt")
			thresh =int(values[group%4])  # int(values[group%4,2])
			print "Running channel:", channel, "the used threshold is:", thresh, "With amplitude:", amplitude
			print "The dataset is:", dataset
			runID = run_control.incrementRunNumber(outdirname)
			print("Run ID: {}".format(runID))
			runName = "run"+str(runID)

			outfile=baseDir+'/'+runName+'internalTrigTest_group_'+str(group)+'_channel_'+str(channel)+'_delay_'+str(trigDelay)+'.tio'
			tempFile = baseDir + runName + "extTest_temperature.log"
			tf = open(tempFile,'w')
			print "Writing Threshodl for group", group%4, "on asic", group/4
			thresh_name='Thresh_'+str(int(group%4))
			module.WriteTriggerASICSetting(thresh_name,int(group/4),thresh, True)
			module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers

			listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
			listener.AddDAQListener(my_ip)
			listener.StartListening()
			writer = target_io.EventFileWriter(outfile, kNPacketsPerEvent, kPacketSize)
			buf = listener.GetEventBuffer()
			writer.StartWatchingBuffer(buf)

			####start data taking


			#print "The input amplitude is:", amplitude/1000.0
			#fg.apply_pulse(1000, amplitude/1000.0, 0,10)
			#time.sleep(1)
			module.WriteSetting("TACK_EnableTrigger", setting)  # enable relevant trigger.

			time.sleep(1)

			module.WriteSetting("TACK_EnableTrigger", 0)  # disable all triggers

			#fg.send_cmd("OUTPut1 OFF")
			ret, temp =  module.GetTempI2CAux()
			currentTime = time.time()
			tf.write("%d    %f    \n" % (currentTime, temp) )

			#time.sleep(1)
			tf.close()
			####close connection to module and output file
			writer.StopWatchingBuffer()  # stops data storing in file

			buf.Flush()
			writer.Close()


	piCom.setChannel(ssh,0)




module.CloseSockets()

#raw_input("Is the trigger powered OFF?")

bps.powerModuleOff()
